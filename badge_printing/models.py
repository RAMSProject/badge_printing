from badge_printing import *

@Session.model_mixin
class Attendee:
    times_printed = Column(Integer, default=0)
    print_pending = Column(Boolean, default=False)

    @presave_adjustment
    def assign_number_after_payment(self):
        if c.AT_THE_CON:
            if self.has_personalized_badge and not self.badge_num:
                if self.paid != c.NOT_PAID:
                    self.badge_num = self.session.next_badge_num(self.badge_type, old_badge_num=0)

    @presave_adjustment
    def print_ready_before_event(self):
        if c.PRE_CON:
            if self.badge_status == c.COMPLETED_STATUS and self.times_printed < 1:
                self.print_pending = True

    @cost_property
    def reprint_cost(self):
        return c.BADGE_REPRINT_FEE

@Session.model_mixin
class SessionMixin:
    def filter_badges_for_printing(self, badge_list, **params):
        """
        Allows batch printing by grouping badges via the passed-in parameters.

        :return:
        """

        if 'badge_type' in params:
            return badge_list.filter(Attendee.badge_type == params['badge_type'])
        elif 'dealer_only' in params:
            return badge_list.filter(Attendee.ribbon.in_([c.DEALER_RIBBON, c.DEALER_ASST_RIBBON]))
        elif 'badge_upgrade' in params:
            return badge_list.filter(Attendee.amount_extra == params['badge_upgrade'])
        else:
            return badge_list
