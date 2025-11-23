from msal import PublicClientApplication
import sdmx


# CLIENT_ID = "11c19a4a-7d9a-498a-8901-2c7aeb199585"
CLIENT_ID = "446ce2fa-88b1-436c-b8e6-94491ca4f6fb"
AUTHORITY = "https://imfprdb2c.b2clogin.com/imfprdb2c.onmicrosoft.com/b2c_1a_signin_aad_simple_user_journey/"
SCOPES = [
    "https://imfprdb2c.onmicrosoft.com/4042e178-3e2f-4ff9-ac38-1276c901c13d/iData.Login",
]


def headers():
    return {}
    app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)
    token = app.acquire_token_interactive(scopes=SCOPES)
    headers = {"Authorization": f"{token['token_type']} {token['access_token']}"}
    return headers


def client(*args, **kwargs):
    client = sdmx.Client(*args, **kwargs)
    client.session.headers.update(headers())
    return client
