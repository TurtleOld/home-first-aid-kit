from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Family, Invitation, Membership
from accounts.serializers import tokens_for_user

User = get_user_model()


@override_settings(
    SECRET_KEY="test-secret-key-with-enough-length-for-jwt-signing",
    SIMPLE_JWT={"SIGNING_KEY": "test-secret-key-with-enough-length-for-jwt-signing"},
)
class AuthInvitationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def register_admin(self, username="admin", family_name="Main family"):
        response = self.client.post(
            "/api/auth/register",
            {
                "username": username,
                "password": "strong-password-123",
                "family_name": family_name,
                "email": f"{username}@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response

    def create_family_admin(self, username, family_name):
        user = User.objects.create_user(username=username, password="strong-password-123")
        family = Family.objects.create(name=family_name)
        Membership.objects.create(user=user, family=family, role=Membership.Role.ADMIN)
        return user, family, tokens_for_user(user)["access"]

    def test_registration_closes_after_first_admin(self):
        status_response = self.client.get("/api/auth/registration-status")
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertTrue(status_response.data["open"])

        self.register_admin()

        status_response = self.client.get("/api/auth/registration-status")
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertFalse(status_response.data["open"])

        second_response = self.client.post(
            "/api/auth/register",
            {
                "username": "second",
                "password": "strong-password-123",
                "family_name": "Second family",
            },
            format="json",
        )
        self.assertEqual(second_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(username="second").exists())
        self.assertEqual(Family.objects.count(), 1)

    def test_logout_blacklists_refresh_token(self):
        register_response = self.register_admin()
        access = register_response.data["access"]
        refresh = register_response.data["refresh"]

        logout_response = self.client.post(
            "/api/auth/logout",
            {"refresh": refresh},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        refresh_response = self.client.post(
            "/api/auth/refresh",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post("/api/auth/logout", {"refresh": "irrelevant"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_is_rate_limited(self):
        self.register_admin()

        for _ in range(5):
            response = self.client.post(
                "/api/auth/login",
                {"username": "admin", "password": "wrong-password"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        throttled_response = self.client.post(
            "/api/auth/login",
            {"username": "admin", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(throttled_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_admin_registers_invites_and_member_accepts(self):
        register_response = self.register_admin()
        admin_access = register_response.data["access"]
        family_id = register_response.data["family"]["id"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access}")
        invite_response = self.client.post("/api/invitations", {}, format="json")
        self.assertEqual(invite_response.status_code, status.HTTP_201_CREATED, invite_response.data)
        token = invite_response.data["token"]

        self.client.credentials()
        public_response = self.client.get(f"/api/invitations/{token}")
        self.assertEqual(public_response.status_code, status.HTTP_200_OK, public_response.data)
        self.assertTrue(public_response.data["is_valid"])

        accept_response = self.client.post(
            f"/api/invitations/{token}/accept",
            {
                "username": "member",
                "password": "strong-password-123",
                "email": "member@example.com",
            },
            format="json",
        )
        self.assertEqual(accept_response.status_code, status.HTTP_201_CREATED, accept_response.data)
        self.assertEqual(accept_response.data["family"]["id"], family_id)
        self.assertEqual(accept_response.data["role"], Membership.Role.MEMBER)

        self.assertEqual(Membership.objects.count(), 2)
        self.assertTrue(
            Membership.objects.filter(
                user__username="admin",
                family_id=family_id,
                role=Membership.Role.ADMIN,
            ).exists()
        )
        self.assertTrue(
            Membership.objects.filter(
                user__username="member",
                family_id=family_id,
                role=Membership.Role.MEMBER,
            ).exists()
        )
        self.assertFalse(Invitation.objects.get(token=token).is_valid)

    def test_family_admin_sees_only_own_invitations(self):
        first = self.register_admin(username="first", family_name="First")
        second_user, second_family, _ = self.create_family_admin("second", "Second")

        first_user = User.objects.get(username="first")
        first_family = Membership.objects.get(user=first_user).family
        first_invite = Invitation.objects.create(
            family=first_family,
            created_by=first_user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        Invitation.objects.create(
            family=second_family,
            created_by=second_user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first.data['access']}")
        list_response = self.client.get("/api/invitations")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK, list_response.data)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["token"], str(first_invite.token))

        revoke_response = self.client.delete(f"/api/invitations/{first_invite.id + 1}")
        self.assertEqual(revoke_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_create_invitation(self):
        register_response = self.register_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}")
        invite_response = self.client.post("/api/invitations", {}, format="json")
        token = invite_response.data["token"]

        self.client.credentials()
        accept_response = self.client.post(
            f"/api/invitations/{token}/accept",
            {"username": "member", "password": "strong-password-123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {accept_response.data['access']}")

        forbidden_response = self.client.post("/api/invitations", {}, format="json")
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_password_change_success(self):
        register_response = self.register_admin()
        access = register_response.data["access"]
        refresh = register_response.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            "/api/auth/password",
            {"current_password": "strong-password-123", "new_password": "even-stronger-456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        old_refresh_response = self.client.post("/api/auth/refresh", {"refresh": refresh}, format="json")
        self.assertEqual(old_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

        login_response = self.client.post(
            "/api/auth/login",
            {"username": "admin", "password": "even-stronger-456"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_password_change_requires_correct_current_password(self):
        register_response = self.register_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}")

        response = self.client.post(
            "/api/auth/password",
            {"current_password": "wrong-password", "new_password": "even-stronger-456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_family_admin_lists_members_and_resets_member_password(self):
        register_response = self.register_admin()
        admin_access = register_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access}")
        invite_response = self.client.post("/api/invitations", {}, format="json")
        token = invite_response.data["token"]

        self.client.credentials()
        accept_response = self.client.post(
            f"/api/invitations/{token}/accept",
            {"username": "member", "password": "strong-password-123"},
            format="json",
        )
        member_id = accept_response.data["user"]["id"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access}")
        members_response = self.client.get("/api/members")
        self.assertEqual(members_response.status_code, status.HTTP_200_OK, members_response.data)
        usernames = {member["user"]["username"] for member in members_response.data}
        self.assertEqual(usernames, {"admin", "member"})

        reset_response = self.client.post(
            f"/api/members/{member_id}/password",
            {"new_password": "brand-new-password-789"},
            format="json",
        )
        self.assertEqual(reset_response.status_code, status.HTTP_204_NO_CONTENT)

        login_response = self.client.post(
            "/api/auth/login",
            {"username": "member", "password": "brand-new-password-789"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_member_cannot_list_members_endpoint_used_by_non_admin(self):
        register_response = self.register_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}")
        invite_response = self.client.post("/api/invitations", {}, format="json")
        token = invite_response.data["token"]

        self.client.credentials()
        accept_response = self.client.post(
            f"/api/invitations/{token}/accept",
            {"username": "member", "password": "strong-password-123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {accept_response.data['access']}")

        members_response = self.client.get("/api/members")
        self.assertEqual(members_response.status_code, status.HTTP_200_OK)

        reset_response = self.client.post(
            "/api/members/1/password",
            {"new_password": "brand-new-password-789"},
            format="json",
        )
        self.assertEqual(reset_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_reset_password_for_other_family_member(self):
        first = self.register_admin(username="first", family_name="First")
        second_user, _, _ = self.create_family_admin("second", "Second")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first.data['access']}")
        response = self.client.post(
            f"/api/members/{second_user.id}/password",
            {"new_password": "brand-new-password-789"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_registration_ignores_is_staff_and_is_superuser(self):
        response = self.client.post(
            "/api/auth/register",
            {
                "username": "admin",
                "password": "strong-password-123",
                "family_name": "Main family",
                "is_staff": True,
                "is_superuser": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        user = User.objects.get(username="admin")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_invitation_accept_ignores_is_staff_and_is_superuser(self):
        register_response = self.register_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}")
        invite_response = self.client.post("/api/invitations", {}, format="json")
        token = invite_response.data["token"]

        self.client.credentials()
        accept_response = self.client.post(
            f"/api/invitations/{token}/accept",
            {
                "username": "member",
                "password": "strong-password-123",
                "is_staff": True,
                "is_superuser": True,
            },
            format="json",
        )
        self.assertEqual(accept_response.status_code, status.HTTP_201_CREATED, accept_response.data)

        user = User.objects.get(username="member")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_other_family_member_cannot_revoke_invitation(self):
        first = self.register_admin(username="first", family_name="First")
        _, _, second_access = self.create_family_admin("second", "Second")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first.data['access']}")
        invite_response = self.client.post("/api/invitations", {}, format="json")
        invite_id = invite_response.data["id"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {second_access}")
        response = self.client.delete(f"/api/invitations/{invite_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Invitation.objects.get(id=invite_id).is_active)
