from odoo import models, _
from odoo.exceptions import UserError

class RecordCleanup(models.AbstractModel):
    _name = 'universal_data_import.record_cleanup'
    _description = 'Universal Record Cleanup'
    
    def cleanup_unused_records(
        self,
        model_name,
        protected_sources=None,
        batch_size=300,
        parity=None,
        domain=None
    ):
        Records = self.env[model_name].sudo()

        protected_ids = set()

        if protected_sources:
            for source_model, source_field in protected_sources:
                records = (
                    self.env[source_model]
                    .sudo()
                    .with_context(active_test=False)
                    .search([])
                )

                protected_ids.update(
                    records.mapped(source_field).ids
                )

        search_domain = []

        if protected_ids:
            search_domain.append(('id', 'not in', list(protected_ids)))

        # Tambahkan filter kustom jika diberikan
        if domain:
            search_domain.extend(domain)

        records = Records.search(
            search_domain,
            order='id'
        )
    
        if not records:
            return {
                'completed': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Completed'),
                    'message': _('There are no more records to delete.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        if parity == 'odd':
            records = records.filtered(lambda r: r.id % 2 == 1)
        elif parity == 'even':
            records = records.filtered(lambda r: r.id % 2 == 0)
        
        records = records[:batch_size]
        
        deleted_count = len(records)
        records.unlink()
    
        return {
            'completed': False,
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Complete'),
                'message': _(
                    '%s records have been deleted. '
                    'Run the action again to process the next batch.'
                ) % deleted_count,
                'type': 'success',
                'sticky': False,
            }
        }