from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_referral_invite_email(referral):
    try:
        ambassador_name = referral.ambassador.user.get_full_name()
        invite_link = f"{settings.FRONTEND_URL}/register?token={referral.invite_token}"
        discount_percentage = referral.discount_percentage

        subject = f"{ambassador_name} invited you to LandKeeper"

        text_content = f"""
        Hi,

        {ambassador_name} has invited you to join LandKeeper.

        Register using the link below and get {discount_percentage}% off your first plan:
        {invite_link}

        If you weren't expecting this invite, you can safely ignore this email.

        Best regards,
        LandKeeper Team
        """

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f4f6f9; margin: 0; padding: 40px 20px;">
            <div style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

                <div style="background: #2E7D32; padding: 40px 20px; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 28px; font-weight: 700; margin: 0;">LandKeeper</h1>
                    <p style="color: #C8E6C9; font-size: 14px; margin-top: 6px;">Land Management CRM</p>
                </div>

                <div style="padding: 40px;">
                    <p style="font-size: 18px; font-weight: 600; color: #1a1a1a; margin-bottom: 16px;">
                        Hi there,
                    </p>
                    <p style="font-size: 15px; color: #555; line-height: 1.7; margin-bottom: 24px;">
                        <strong>{ambassador_name}</strong> has invited you to join <strong>LandKeeper</strong> —
                        a simple way to manage rental properties, tenants, and finances in one place.
                    </p>

                    <div style="background: #E8F5E9; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 32px;">
                        <p style="font-size: 13px; color: #2E7D32; margin: 0 0 4px 0; font-weight: 600;">
                            SIGN UP NOW AND GET
                        </p>
                        <p style="font-size: 26px; color: #2E7D32; margin: 0; font-weight: 700;">
                            {discount_percentage}% OFF
                        </p>
                        <p style="font-size: 13px; color: #558B2F; margin: 4px 0 0 0;">
                            your first plan
                        </p>
                    </div>

                    <div style="text-align: center; margin-bottom: 32px;">
                        <a href="{invite_link}"
                           style="display: inline-block; background: #2E7D32; color: #ffffff; text-decoration: none; padding: 14px 36px; border-radius: 8px; font-size: 15px; font-weight: 600;">
                            Accept Invitation
                        </a>
                    </div>

                    <hr style="border: none; border-top: 1px solid #f0f0f0; margin: 32px 0;">

                    <div style="background: #FFF8E1; border-left: 4px solid #FFC107; padding: 14px 18px; border-radius: 6px; margin-top: 24px;">
                        <p style="font-size: 13px; color: #7a6200; line-height: 1.6;">
                            ⚠️ If you weren't expecting this invite, you can safely ignore this email.
                        </p>
                    </div>
                </div>

                <div style="background: #f9f9f9; padding: 24px 40px; text-align: center; border-top: 1px solid #f0f0f0;">
                    <p style="font-size: 12px; color: #aaa; line-height: 1.8; margin: 0;">
                        © 2026 LandKeeper. All rights reserved.<br>
                        This is an automated email, please do not reply.
                    </p>
                </div>

            </div>
        </body>
        </html>
        """

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[referral.invited_email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()
        return True

    except Exception as e:
        print(f"Email error: {e}")
        return False
