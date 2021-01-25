from odoo import api, fields, models

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    
    def reservations_check(self):
        
        quants = self.search([])
        move_line_ids = []
        warning = ''
        for quant in quants:
            move_lines = env["stock.move.line"].search([
                ('product_id', '=', quant.product_id.id),
                ('location_id', '=', quant.location_id.id),
                ('lot_id', '=', quant.lot_id.id),
                ('package_id', '=', quant.package_id.id),
                ('owner_id', '=', quant.owner_id.id),
                ('product_qty', '!=', 0)
            ])
            move_line_ids += move_lines.ids
            reserved_on_move_lines = sum(move_lines.mapped('product_qty'))
            move_line_str = str.join(', ', [str(move_line_id) for move_line_id in move_lines.ids])

            if quant.location_id.should_bypass_reservation():
                # If a quant is in a location that should bypass the reservation, its `reserved_quantity` field
                # should be 0.
                if quant.reserved_quantity != 0:
                    warning += "Problematic quant found: %s (quantity: %s, reserved_quantity: %s)\n" % (quant.id, quant.quantity, quant.reserved_quantity)
                    warning += "its `reserved_quantity` field is not 0 while its location should bypass the reservation\n"
                    if move_lines:
                        warning += "These move lines are reserved on it: %s (sum of the reservation: %s)\n" % (move_line_str, reserved_on_move_lines)
                    else:
                        warning += "no move lines are reserved on it, you can safely reset its `reserved_quantity` to 0\n"
                    warning += '******************\n'
            else:
                # If a quant is in a reservable location, its `reserved_quantity` should be exactly the sum
                # of the `product_qty` of all the partially_available / assigned move lines with the same
                # characteristics.
                if quant.reserved_quantity == 0:
                    if move_lines:
                        warning += "Problematic quant found: %s (quantity: %s, reserved_quantity: %s)\n" % (quant.id, quant.quantity, quant.reserved_quantity)
                        warning += "its `reserved_quantity` field is 0 while these move lines are reserved on it: %s (sum of the reservation: %s)\n" % (move_line_str, reserved_on_move_lines)
                        warning += '******************\n'
                elif quant.reserved_quantity < 0:
                    warning += "Problematic quant found: %s (quantity: %s, reserved_quantity: %s)\n" % (quant.id, quant.quantity, quant.reserved_quantity)
                    warning += "its `reserved_quantity` field is negative while it should not happen\n"
                    if move_lines:
                        warning += "These move lines are reserved on it: %s (sum of the reservation: %s)\n" % (move_line_str, reserved_on_move_lines)
                    warning += '******************\n'
                else:
                    if reserved_on_move_lines != quant.reserved_quantity:
                        warning += "Problematic quant found: %s (quantity: %s, reserved_quantity: %s)\n" % (quant.id, quant.quantity, quant.reserved_quantity)
                        warning += "its `reserved_quantity` does not reflect the move lines reservation\n"
                        warning += "These move lines are reserved on it: %s (sum of the reservation: %s)\n" % (move_line_str, reserved_on_move_lines)
                        warning += '******************\n'
                    else:
                      if any(move_line.product_qty < 0 for move_line in move_lines):
                        warning += "Problematic quant found: %s (quantity: %s, reserved_quantity: %s)\n" % (quant.id, quant.quantity, quant.reserved_quantity)
                        warning += "its `reserved_quantity` correctly reflects the move lines reservation but some are negatives\n"
                        warning += "These move lines are reserved on it: %s (sum of the reservation: %s)\n" % (move_line_str, reserved_on_move_lines)
                        warning += '******************\n'

        move_lines = env['stock.move.line'].search([('product_id.type', '=', 'product'), ('product_qty', '!=', 0), ('id', 'not in', move_line_ids)])

        for move_line in move_lines:
            if move_line.state in ('done', 'cancel'):
               warning += "Problematic move line found: %s (reserved_quantity: %s)\n" % (move_line.id, move_line.product_qty)
               warning += "It has a `reserved_quantity` despite its status %r\n" % (move_line.state,)
               warning += '******************\n'
                   reserved_on_move_lines -= move_line.product_qty
            if not move_line.location_id.should_bypass_reservation():
               warning += "Problematic move line found: %s (reserved_quantity: %s)\n" % (move_line.id, move_line.product_qty)
               warning += "There is no existing quants despite its `reserved_quantity`\n"
               warning += '******************\n'

        if warning == '':
            warning = 'nothing seems wrong'
        return warning
