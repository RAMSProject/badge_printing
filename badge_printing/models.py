from badge_printing import *

@Session.model_mixin
class SessionMixin:
    def get_next_badge_to_print(self, minor=''):
        badge_list = self.query(Attendee) \
            .filter(Attendee.print_pending, Attendee.birthdate != None, Attendee.badge_num != None) \
            .order_by(Attendee.badge_num).all()

        try:
            if minor:
                attendee = next(badge for badge in badge_list if badge.age_now_or_at_con < 18)
            else:
                attendee = next(badge for badge in badge_list if badge.age_now_or_at_con >= 18)
        except StopIteration:
            return None

        attendee.times_printed += 1
        attendee.print_pending = False
        self.add(attendee)
        self.commit()

        return attendee

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
            if self.badge_status == c.COMPLETED_STATUS and not self.is_not_ready_to_checkin:
                self.print_pending = True

    @presave_adjustment
    def print_ready_at_event(self):
        if c.AT_THE_CON:
            if self.checked_in and self.times_printed < 1:
                self.print_pending = True

    @cost_property
    def reprint_cost(self):
        return c.BADGE_REPRINT_FEE

    @property
    def age_now_or_at_con(self):
        if not self.birthdate:
            return None
        day = c.EPOCH.date() if date.today() <= c.EPOCH.date() else sa.localized_now().date()
        return day.year - self.birthdate.year - ((day.month, day.day) < (self.birthdate.month, self.birthdate.day))
