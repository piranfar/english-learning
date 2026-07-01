import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tutor.utils.provider_access import resolve_user_provider
from tutor.utils.uploads import AudioUploadTooLarge, validate_audio_upload

User = get_user_model()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class SecurityAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="secauthuser",
            password="testpass123",
        )

    def test_login_works_with_csrf_token(self):
        self.client.get("/api/csrf/")
        token = self.client.cookies["csrftoken"].value
        response = self.client.post(
            "/api/auth/login/",
            {"username": "secauthuser", "password": "testpass123"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])

    def test_login_without_csrf_is_rejected(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "secauthuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class SecuritySettingsTests(TestCase):
    def test_debug_false_without_secret_key_raises(self):
        env = os.environ.copy()
        env["DJANGO_DEBUG"] = "false"
        env["DJANGO_SKIP_DOTENV"] = "1"
        env.pop("DJANGO_SECRET_KEY", None)
        env.pop("SECRET_KEY", None)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os; os.environ['DJANGO_DEBUG']='false'; "
                "os.environ['DJANGO_SKIP_DOTENV']='1'; "
                "os.environ.pop('DJANGO_SECRET_KEY', None); "
                "os.environ.pop('SECRET_KEY', None); "
                "import core.settings",
            ],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = (result.stdout or "") + (result.stderr or "")
        self.assertIn("DJANGO_SECRET_KEY", combined)


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
    MAX_AUDIO_UPLOAD_BYTES=128,
)
class SecurityUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploaduser",
            password="testpass123",
        )
        self.client.login(username="uploaduser", password="testpass123")

    def test_validate_audio_upload_rejects_large_file(self):
        upload = SimpleUploadedFile("clip.webm", b"x" * 256, content_type="audio/webm")
        with self.assertRaises(AudioUploadTooLarge):
            validate_audio_upload(upload)

    def test_oversized_transcribe_returns_413(self):
        audio = SimpleUploadedFile("clip.webm", b"x" * 256, content_type="audio/webm")
        response = self.client.post(
            "/api/transcribe/",
            {"audio": audio},
            format="multipart",
        )
        self.assertEqual(response.status_code, 413)


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
    ALLOW_LEARNER_PROVIDER_OVERRIDE=False,
)
class SecurityProviderOverrideTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.learner = User.objects.create_user(
            username="learneroverride",
            password="testpass123",
        )
        self.staff = User.objects.create_user(
            username="staffoverride",
            password="testpass123",
            is_staff=True,
        )

    def test_resolve_user_provider_non_staff_returns_none(self):
        request = type("Req", (), {"user": self.learner})()
        self.assertIsNone(resolve_user_provider(request, "anthropic"))

    def test_resolve_user_provider_staff_returns_value(self):
        request = type("Req", (), {"user": self.staff})()
        self.assertEqual(resolve_user_provider(request, "anthropic"), "anthropic")

    @patch("tutor.services.generate_from_template")
    def test_non_staff_provider_override_ignored(self, mock_generate):
        mock_generate.return_value = (
            "intro\n---READING_ANALYSIS---\n"
            '{"vocabulary":[],"main_idea":"x","summary":"y",'
            '"comprehension_questions":[],"grammar_points":[],"speaking_questions":[]}\n'
            "---END_READING_ANALYSIS---"
        )
        self.client.login(username="learneroverride", password="testpass123")
        response = self.client.post(
            "/api/reading/analyze/",
            {
                "passage": "A short passage about learning English every day.",
                "provider": "anthropic",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        mock_generate.assert_called_once()
        self.assertIsNone(mock_generate.call_args.kwargs.get("provider"))

    @patch("tutor.services.generate_from_template")
    def test_staff_provider_override_allowed(self, mock_generate):
        mock_generate.return_value = (
            "intro\n---READING_ANALYSIS---\n"
            '{"vocabulary":[],"main_idea":"x","summary":"y",'
            '"comprehension_questions":[],"grammar_points":[],"speaking_questions":[]}\n'
            "---END_READING_ANALYSIS---"
        )
        self.client.login(username="staffoverride", password="testpass123")
        response = self.client.post(
            "/api/reading/analyze/",
            {
                "passage": "A short passage about learning English every day.",
                "provider": "anthropic",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        mock_generate.assert_called_once()
        self.assertEqual(mock_generate.call_args.kwargs.get("provider"), "anthropic")
