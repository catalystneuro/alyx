# Register the modules to show up at the admin page https://server/admin
from django.contrib import admin


class FoodConsumptionAmountForm(BaseActionForm):
    def __init__(self, *args, **kwargs):
        super(FoodConsumptionAmountForm, self).__init__(*args, **kwargs)
        if self.fields.keys():
            self.fields['food_amount'].widget.attrs.update({'autofocus': 'autofocus'})


class FoodConsumptionAmountAdmin(BaseActionAdmin):
    list_display = ['subject_l', 'weight', 'percentage_weight', 'date_time', 'projects']
    list_select_related = ('subject',)
    fields = ['subject', 'date_time', 'weight', 'user']
    ordering = ('-date_time',)
    list_display_links = ('weight',)
    search_fields = ['subject__nickname', 'subject__projects__name']
    list_filter = [ResponsibleUserListFilter,
                   ('subject', RelatedDropdownFilter)]

    form = FoodConsumptionAmountForm
