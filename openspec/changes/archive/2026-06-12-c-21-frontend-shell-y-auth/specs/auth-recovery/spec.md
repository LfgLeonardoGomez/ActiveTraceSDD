# Auth Recovery — Spec

> Forgot password and reset password flows.

---

## REQ-RECOV-01: ForgotPasswordForm renders email input

A simple form that collects the user's email to request a password reset link.

### Scenarios

**Scenario 1: ForgotPasswordForm renders correctly**
GIVEN the user navigates to /forgot-password
WHEN the ForgotPasswordForm renders
THEN an email input field labeled "Email" is visible
AND a submit button labeled "Enviar instrucciones" is visible
AND a link "Volver al inicio de sesión" navigates to /login

**Scenario 2: Empty email shows validation error**
GIVEN the ForgotPasswordForm is displayed
WHEN the user clicks submit without entering an email
THEN a Zod error "Email inválido" appears
AND no request is sent to the API

**Scenario 3: Invalid email format shows validation error**
GIVEN the ForgotPasswordForm is displayed
WHEN the user types "not-email" and submits
THEN a Zod error "Email inválido" appears
AND no request is sent to the API

---

## REQ-RECOV-02: On submit, POST /api/auth/forgot -> always show "Si el email existe, recibirás instrucciones"

The endpoint always returns 202 to prevent email enumeration. The UI message is the same regardless of whether the email exists.

### Scenarios

**Scenario 1: Valid email exists**
GIVEN the ForgotPasswordForm is displayed
WHEN the user submits a valid email that exists in the system
THEN a POST request is sent to /api/auth/forgot with { email }
AND the response is 202
AND the form displays "Si el email existe, recibirás instrucciones"
AND the submit button is disabled for 30 seconds (rate limit on resend)
AND a countdown "Reenviar en {seconds}s" is shown on the disabled button

**Scenario 2: Valid email does NOT exist**
GIVEN the ForgotPasswordForm is displayed
WHEN the user submits a valid email that does not exist in the system
THEN a POST request is sent to /api/auth/forgot with { email }
AND the response is 202 (same as existing email — no enumeration)
AND the form displays "Si el email existe, recibirás instrucciones"

**Scenario 3: Loading state during submission**
GIVEN the ForgotPasswordForm is displayed
WHEN the user submits a valid email
AND the API request is in flight
THEN the submit button shows a Spinner
AND the submit button is disabled
AND the email input is disabled

---

## REQ-RECOV-03: ResetPasswordForm renders token (hidden) + new password + confirm password

The reset form is accessed via a signed link from email; the token is embedded in the URL.

### Scenarios

**Scenario 1: ResetPasswordForm renders with token from URL**
GIVEN the user navigates to /reset-password?token=abc123
WHEN the ResetPasswordForm renders
THEN a hidden input stores the token from the URL query parameter
AND a password input labeled "Nueva contraseña" is visible
AND a password input labeled "Confirmar contraseña" is visible
AND a submit button labeled "Restablecer contraseña" is visible

**Scenario 2: Missing token redirects to forgot-password**
GIVEN the user navigates to /reset-password without a token query parameter
WHEN the ResetPasswordPage loads
THEN the user is redirected to /forgot-password
AND a message "Enlace inválido. Solicitá un nuevo restablecimiento." is displayed

---

## REQ-RECOV-04: Validation: password >= 8 chars, passwords must match

Client-side validation ensures password strength and confirmation match before submission.

### Scenarios

**Scenario 1: Short password shows validation error**
GIVEN the ResetPasswordForm is displayed
WHEN the user types "abc" in the password field and submits
THEN a Zod error "La contraseña debe tener al menos 8 caracteres" appears
AND no request is sent to the API

**Scenario 2: Passwords do not match**
GIVEN the ResetPasswordForm is displayed
WHEN the user types "password123" in the password field
AND "password456" in the confirm field
AND submits
THEN a Zod error "Las contraseñas no coinciden" appears
AND no request is sent to the API

**Scenario 3: Both validations pass**
GIVEN the ResetPasswordForm is displayed
WHEN the user types "newStrongPassword42" in both fields
AND submits
THEN the form passes client-side validation
AND a POST request is sent to the API

---

## REQ-RECOV-05: On submit, POST /api/auth/reset with token + new_password

The submitted form sends the reset token and new password to the backend.

### Scenarios

**Scenario 1: Valid submission**
GIVEN the ResetPasswordForm passes client-side validation
WHEN the user clicks submit
THEN a POST request is sent to /api/auth/reset
WITH body containing token (from URL) and new_password
AND the submit button shows a Spinner
AND the password inputs are disabled during the request

---

## REQ-RECOV-06: On 204 -> redirect to /login with success message

Successful password reset clears the form and redirects to the login page.

### Scenarios

**Scenario 1: Successful reset redirects to login**
GIVEN the user submitted a valid token and new password
WHEN POST /api/auth/reset returns 204
THEN the user is redirected to /login
AND a success message "Contraseña restablecida con éxito. Iniciá sesión." is displayed as a toast or banner

**Scenario 2: 204 clears any previous error state**
GIVEN the user previously received a 400 error
WHEN the user fixes the issue and resubmits
AND the API returns 204
THEN the previous error messages are cleared
AND the user is redirected to /login

---

## REQ-RECOV-07: On 400 -> show "Token inválido o expirado"

Invalid or expired reset tokens return a user-friendly error with guidance.

### Scenarios

**Scenario 1: Invalid token**
GIVEN the ResetPasswordForm is displayed
WHEN the user submits a valid new password
AND POST /api/auth/reset returns 400 with detail "token invalid or expired"
THEN the form displays "Token inválido o expirado. Solicitá un nuevo restablecimiento."
AND a link "Solicitar nuevo restablecimiento" navigates to /forgot-password

**Scenario 2: Previously used token**
GIVEN the ResetPasswordForm is displayed
WHEN the user submits a token that was already used to reset the password
AND POST /api/auth/reset returns 400
THEN the form displays "Token inválido o expirado. Solicitá un nuevo restablecimiento."
AND the password fields are cleared

**Scenario 3: Loading error recovery**
GIVEN the ResetPasswordForm displayed a 400 error
WHEN the user starts typing in either password field
THEN the error message is cleared
AND the user can attempt to submit again (same token)
