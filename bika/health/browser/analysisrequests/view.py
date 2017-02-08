from bika.lims.browser.analysisrequest import AnalysisRequestsView as BaseView
from bika.lims.browser.bika_listing import BikaListingFilterBar\
    as BaseBikaListingFilterBar
from bika.health import bikaMessageFactory as _
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.public import DisplayList
import json
from bika.health.catalog import CATALOG_PATIENT_LISTING
from datetime import datetime, date


class AnalysisRequestsView(BaseView):
    def __init__(self, context, request):
        super(AnalysisRequestsView, self).__init__(context, request)
        self.patient_catalog = None
        self.columns['BatchID']['title'] = _('Case ID')

    def folderitems(self, full_objects=False):
        pm = getToolByName(self.context, "portal_membership")
        member = pm.getAuthenticatedMember()
        # We will use this list for each element
        roles = member.getRoles()
        if 'Manager' in roles \
            or 'LabManager' in roles \
                or 'LabClerk' in roles:
            # Add Client Patient fields
            self.columns['getPatientID'] = {
                'title': _('Patient ID'),
                'toggle': True}
            self.columns['getClientPatientID'] = {
                'title': _("Client PID"),
                'toggle': True}
            self.columns['getPatient'] = {
                'title': _('Patient'),
                'toggle': True}
            for rs in self.review_states:
                i = rs['columns'].index('BatchID') + 1
                rs['columns'].insert(i, 'getClientPatientID')
                rs['columns'].insert(i, 'getPatientID')
                rs['columns'].insert(i, 'getPatient')
        # Setting ip the patient catalog to be used in folderitem()
        self.patient_catalog = getToolByName(
            self.context, CATALOG_PATIENT_LISTING)
        return super(AnalysisRequestsView, self).folderitems(
            full_objects=False, classic=False)

    def folderitem(self, obj, item, index):
        item = super(AnalysisRequestsView, self)\
            .folderitem(obj, item, index)
        patient = self.patient_catalog(UID=obj.getPatientUID)
        if patient:
            item['getPatientID'] = patient[0].getId
            item['replace']['getPatientID'] = "<a href='%s'>%s</a>" % \
                (patient[0].getURL(), patient[0].getId)
            item['getClientPatientID'] = patient[0].getClientPatientID
            item['replace']['getClientPatientID'] = "<a href='%s'>%s</a>" % \
                (patient[0].getURL(), patient[0].getClientPatientID)
            item['getPatient'] = patient[0].Title
            item['replace']['getPatient'] = "<a href='%s'>%s</a>" % \
                (patient[0].getURL(), patient[0].Title)
        return item

    def isItemAllowed(self, obj):
        """
        Checks the BikaLIMS conditions and also checks filter bar conditions
        @Obj: it is an analysis request brain.
        @return: boolean
        """
        if not super(AnalysisRequestsView, self).isItemAllowed(obj):
            return False
        return self.filter_bar_check_item(obj)

    def getFilterBar(self):
        """
        This function creates an instance of BikaListingFilterBar if the
        class has not created one yet.
        :return: a BikaListingFilterBar instance
        """
        self._advfilterbar = self._advfilterbar if self._advfilterbar else \
            BikaListingFilterBar(context=self.context, request=self.request)
        return self._advfilterbar


class BikaListingFilterBar(BaseBikaListingFilterBar):
    """
    This class defines a filter bar to make advanced queries in
    BikaListingView. This filter shouldn't override the 'filter by state'
    functionality
    """

    def filter_bar_builder(self):
        """
        The template is going to call this method to create the filter bar in
        bika_listing_filter_bar.pt
        If the method returns None, the filter bar will not be shown.
        :return: a list of dictionaries as the filtering fields or None.
        """
        fields_dict = [{
            'name': 'analysis_name',
            'label': _('Analysis name'),
            'type': 'select',
            'voc': self._getAnalysesNamesVoc(),
        }, {
            'name': 'print_state',
            'label': _('Print state'),
            'type': 'select',
            'voc': self._getPrintStatesVoc(),
        }, {
            'name': 'case',
            'label': _('Cases'),
            'type': 'autocomplete_text',
            'voc': json.dumps(self._getCasesVoc()),
        }, {
            'name': 'date_received',
            'label': _('Date received'),
            'type': 'date_range',
        }, #{
        #    'name': 'date_tested',
        #    'label': _('Date tested'),
        #    'type': 'date_range',
        #},
        ]
        return fields_dict

    def _getAnalysesNamesVoc(self):
        """
        Returns a DisplayList object with analyses names.
        """
        l = self.context.bika_setup.bika_analysisservices.listFolderContents()
        return DisplayList(
            [(element.UID(), element.Title()) for element in l])

    def _getPrintStatesVoc(self):
        """
        Returns a DisplayList object with print states.
        """
        return DisplayList([
            ('0', _('Never printed')),
            ('1', _('Printed after last publish')),
            ('2', _('Printed but republished afterwards')),
            ])

    def _getCasesVoc(self):
        """
        Returns a list object with active cases ids.
        """
        catalog = getToolByName(self.context, "portal_catalog")
        brains = catalog({
            'portal_type': 'Batch',
            'review_state': 'open',
        })
        return [brain.id for brain in brains]

    def get_filter_bar_queryaddition(self):
        """
        This function gets the values from the filter bar inputs in order to
        create a query accordingly.
        Only returns the once that can be added to contentFilter dictionary.
        in this case, the catalog is bika_catalog
        In this case the keys with index representation are:
        - date_received - getDateReceived
        - date_received - BatchUID
        :return: a dictionary to be added to contentFilter.
        """
        query_dict = {}
        filter_dict = self.get_filter_bar_dict()
        # Date received filter
        if filter_dict.get('date_received_0', '') or\
                filter_dict.get('date_received_1', ''):
            date_0 = filter_dict.get('date_received_0') \
                if filter_dict.get('date_received_0', '')\
                else '1900-01-01'
            date_1 = filter_dict.get('date_received_1')\
                if filter_dict.get('date_received_1', '')\
                else datetime.strftime(date.today(), "%Y-%m-%d")
            date_range_query = {
                'query':
                (date_0 + ' 00:00', date_1 + ' 23:59'), 'range': 'min:max'}
            query_dict['getDateReceived'] = date_range_query
        # Batch(case) filter
        if filter_dict.get('case', ''):
            # removing the empty and space values and gettin their UIDs
            clean_list_ids = [
                a.strip() for a in filter_dict.get('case', '').split(',')
                if a.strip()]
            # Now we have the case(batch) ids, lets get their UIDs
            catalog = getToolByName(self, 'bika_catalog')
            brains = catalog(
                portal_type='Batch',
                cancellation_state='active',
                review_state='open',
                id=clean_list_ids
                )
            query_dict['BatchUID'] = [a.UID for a in brains]
        return query_dict

    def filter_bar_check_item(self, item):
        """
        This functions receives a key-value items, and checks if it should be
        displayed.
        It is recomended to be used in isItemAllowed() method.
        This function should be only used for those fields without
        representation as an index in the catalog.
        :item: The item to check. This is a brain
        :return: boolean.
        """
        dbar = self.get_filter_bar_dict()
        keys = dbar.keys()
        final_decision = 'True'
        item_obj = None
        for key in keys:
            #elif key == 'date_tested_0' and d.get(key, '') != '':
            #    import pdb; pdb.set_trace()
            #elif key == 'date_tested_1' and d.get(key, '') != '':
            #    import pdb; pdb.set_trace()
            if key == 'analysis_name' and dbar.get(key, '') != '':
                item_obj = item.getObject() if not item_obj else item_obj
                uids = [
                    analysis.getService().UID() for analysis in
                    item_obj.getAnalyses(full_objects=True)]
                if dbar.get(key, '') not in uids:
                    return False
            if key == 'print_state' and dbar.get(key, '') != '':
                if dbar.get(key, '') != item.getPrinted:
                    return False
        return True
