from badge_printing import *

@all_renderable(c.PEOPLE)
class Root:
    def index(self, session, page='1', message='', id=None, pending='', reprint_reason=''):
        if id:
            attendee = session.attendee(id)
            attendee.badge_status = c.COMPLETED_STATUS
            attendee.for_review += "Automated message: Badge marked for free reprint by {} on {}. Reason: {}"\
                .format(session.admin_attendee().full_name,localized_now().strftime('%m/%d, %H:%M'),reprint_reason)
            session.add(attendee)
            session.commit()
            message = "Badge marked for re-print!"

        if pending:
            badges = session.query(Attendee).filter(Attendee.print_pending).filter(Attendee.badge_status == c.COMPLETED_STATUS).order_by(Attendee.badge_num).all()
        else:
            badges = session.query(Attendee).filter(not Attendee.print_pending).order_by(Attendee.badge_num).all()

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

    def print_badges(self, session, minor=''):
        attendee = session.get_next_badge_to_print(minor=minor)
        if not attendee:
            raise HTTPRedirect('badge_waiting?minor={}'.format(minor))

        badge_type = attendee.badge_type_label

        # Allows events to add custom print overrides
        try:
            badge_type += attendee.extra_print_label
        except:
            pass

        ribbon = attendee.ribbon_label if attendee.ribbon != c.NO_RIBBON else ''

        return {
            'badge_type': badge_type,
            'ribbon': ribbon,
            'badge_num': attendee.badge_num,
            'badge_name': attendee.badge_printed_name,
            'badge': True,
            'minor': minor
        }

    def badge_waiting(self, message='', minor=''):
        return {
            'message': message,
            'minor': minor
        }

    def reprint_fee(self, session, attendee_id=None, message='', fee_amount=0, reprint_reason='', refund=''):
        attendee = session.attendee(attendee_id)
        fee_amount = int(fee_amount)
        if not fee_amount and not reprint_reason:
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
