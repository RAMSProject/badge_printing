from badge_printing import *

@all_renderable(c.PEOPLE)
class Root:
    def index(self, session, page='1', message='', id=None, pending='', reprint_reason=''):
        if id:
            attendee = session.attendee(id)
            attendee.print_pending = True
            attendee.for_review += "Automated message: Badge marked for free reprint by {} on {}. Reason: {}"\
                .format(session.admin_attendee().full_name,localized_now().strftime('%m/%d, %H:%M'),reprint_reason)
            session.add(attendee)
            session.commit()
            message = "Badge marked for re-print!"

        if pending:
            badges = session.query(Attendee).filter(Attendee.print_pending).order_by(Attendee.badge_num).all()
        else:
            badges = session.query(Attendee).filter(Attendee.print_pending == False).filter(Attendee.times_printed > 0)\
                .filter(Attendee.badge_status == c.COMPLETED_STATUS).order_by(Attendee.badge_num).all()

        page = int(page)
        count = len(badges)
        pages = range(1, int(math.ceil(count / 100)) + 1)
        badges = badges[-100 + 100*page : 100*page] if page else []

        return {
            'page':     page,
            'pages':    pages,
            'message':  message,
            'badges':   badges,
            'pending':  pending
        }

    def print_badges(self, session, message='', minor='', **params):
        # TODO: make the minor/not minor distinction AC-only?
        badge_list = session.query(Attendee).filter(Attendee.print_pending).order_by(Attendee.badge_num)
        badge_list = session.filter_badges_for_printing(badge_list, **params)
        badge_list = [row for row in badge_list.all() if row.age_group_conf['min_age'] < 18] if minor else [row for row in badge_list.all() if row.age_group_conf['min_age'] >= 18]

        try:
            attendee = badge_list.pop(0)
        except IndexError:
            if 'batch_printing' in params:
                raise HTTPRedirect('index?message={}'.format("No badges ready to print with those parameters!"))
            else:
                raise HTTPRedirect('badge_waiting?minor={}'.format(minor))

        ribbon_and_or_badge_type = attendee.ribbon_and_or_badge.split(' / ')
        if len(ribbon_and_or_badge_type) > 1:
            badge_type = ribbon_and_or_badge_type[0] + "<br />" + ribbon_and_or_badge_type[1]
        else:
            badge_type = ribbon_and_or_badge_type[0]

        # Allows events to add custom print overrides
        try:
            badge_type += attendee.extra_print_label
        except:
            pass

        attendee.times_printed += 1
        attendee.print_pending = False
        session.add(attendee)
        session.commit()

        return {
            'badge_type': badge_type,
            'badge_num': attendee.badge_num,
            'badge_name': attendee.badge_printed_name,
            'badge': True,
            'message': message,
            'minor': minor,
            'params': params
        }

    def badge_waiting(self, message='', minor='', badge_type=''):
        return {
            'message': message,
            'minor': minor,
            'badge_type': badge_type
        }

    def reprint_fee(self, session, attendee_id=None, message='', fee_amount=0, reprint_reason='', refund=''):
        attendee = session.attendee(attendee_id)
        fee_amount = int(fee_amount)
        if not fee_amount and not reprint_reason and c.BADGE_REPRINT_FEE:
            message = "You must charge a fee or enter a reason for a free reprint!"
        if not fee_amount and refund:
            message = "You can't refund a fee of $0!"

        if not message:
            if not fee_amount:
                attendee.for_review += "Automated message: Badge marked for free reprint by {} on {}. Reason: {}"\
                    .format(session.admin_attendee().full_name,localized_now().strftime('%m/%d, %H:%M'),reprint_reason)
                message = 'Free reprint recorded and badge sent to printer.'
                attendee.print_pending = True
            elif refund:
                attendee.paid = c.REFUNDED
                attendee.amount_refunded += fee_amount
                attendee.for_review += "Automated message: Reprint fee of ${} refunded by {} on {}. Reason: {}"\
                    .format(fee_amount, session.admin_attendee().full_name,localized_now().strftime('%m/%d, %H:%M'),reprint_reason)
                message = 'Reprint fee of ${} refunded.'.format(fee_amount)
            else:
                attendee.amount_paid += fee_amount
                attendee.for_review += "Automated message: Reprint fee of ${} charged by {} on {}. Reason: {}"\
                    .format(fee_amount, session.admin_attendee().full_name,localized_now().strftime('%m/%d, %H:%M'),reprint_reason)
                message = 'Reprint fee of ${} charged. Badge sent to printer.'.format(fee_amount)
                attendee.print_pending = True

        raise HTTPRedirect('../registration/form?id={}&message={}', attendee_id, message)
