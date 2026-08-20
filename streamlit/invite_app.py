import requests

import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Project Invite")

st.title("Project Invite")

invite_token = st.query_params.get("token")

if not invite_token:
    st.error("Invitation token is missing")

tab_login, tab_register = st.tabs(["Sign In", "Register"])

with tab_login:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In & Accept Invite"):
        try:
            login_response = requests.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
                timeout=10,
            )

            if not login_response.ok:
                st.error(login_response.json().get("detail", "Login failed"))
            else:
                access_token = login_response.json()["access_token"]

                join_response = requests.post(
                    f"{API_BASE}/project/join",
                    params={"token": invite_token},
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )

                if join_response.ok:
                    data = join_response.json()

                    st.success(data.get("message", "Successfully joined project"))
                    st.write("Project ID:", data.get("project_id"))

                    st.code(access_token)
                else:
                    st.error(
                        join_response.json().get(
                            "detail",
                            "Failed to accept invitation",
                        )
                    )

        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")


with tab_register:
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    reg_email = st.text_input("Email", key="register_email")
    reg_password = st.text_input(
        "Password",
        type="password",
        key="register_password",
    )

    if st.button("Register & Accept Invite"):
        try:
            register_response = requests.post(
                f"{API_BASE}/auth/register",
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": reg_email,
                    "password": reg_password,
                },
                timeout=10,
            )

            if not register_response.ok:
                st.error(
                    register_response.json().get(
                        "detail",
                        "Registration failed",
                    )
                )
            else:
                login_response = requests.post(
                    f"{API_BASE}/auth/login",
                    json={
                        "email": reg_email,
                        "password": reg_password,
                    },
                    timeout=10,
                )

                if not login_response.ok:
                    st.error("Registered, but login failed")
                else:
                    access_token = login_response.json()["access_token"]

                    join_response = requests.post(
                        f"{API_BASE}/project/join",
                        params={"token": invite_token},
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10,
                    )

                    if join_response.ok:
                        data = join_response.json()

                        st.success(
                            data.get(
                                "message",
                                "Successfully joined project",
                            )
                        )

                        st.write("Project ID:", data.get("project_id"))
                        st.code(access_token)

                    else:
                        st.error(
                            join_response.json().get(
                                "detail",
                                "Failed to accept invitation",
                            )
                        )

        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")
