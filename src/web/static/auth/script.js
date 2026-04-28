import { ROUTES, STORAGE_KEYS } from "../core/config.js";
import { createStateManager } from "./js/storage.js";
import {
  ensureErrorNode,
  validateConfirmPassword,
  validateEmail,
  validatePassword,
  validateUsername,
} from "./js/validation.js";
import {
  bindPasswordToggle,
  bindSwitchLinks,
  bindTextInput,
  restoreState,
  setMode,
} from "./js/ui.js";

document.addEventListener("DOMContentLoaded", function () {
  const root = document.querySelector("[data-active-form]");
  if (!root) return;

  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const authTitle = document.getElementById("auth-title");
  const authSub = document.getElementById("auth-sub");

  const loginPath = root.dataset.loginPath || ROUTES.LOGIN;
  const registerPath = root.dataset.registerPath || ROUTES.REGISTER;

  const loginForm = document.querySelector("#form-login form");
  const registerForm = document.getElementById("reg-form");

  const loginUsername = document.getElementById("login-username");
  const loginPassword = document.getElementById("login-password");

  const registerUsername = document.getElementById("reg-username");
  const registerEmail = document.getElementById("reg-email");
  const registerPassword = document.getElementById("reg-password");
  const registerConfirm = document.getElementById("reg-confirm");

  const loginUsernameError = document.getElementById("login-username-error");
  const loginPasswordError = document.getElementById("login-password-error");
  const registerUsernameError = document.getElementById("reg-username-error");
  const registerEmailError = document.getElementById("reg-email-error");
  const registerPasswordError = document.getElementById("reg-password-error");
  const registerConfirmError = ensureErrorNode(registerConfirm, "confirm-error");

  const defaults = {
    activeForm: root.dataset.activeForm || "login",
    loginUsername: "",
    registerUsername: "",
    registerEmail: "",
  };

  const { readState, writeState } = createStateManager(STORAGE_KEYS.AUTH_STATE, defaults);

  function setActiveMode(mode, persist) {
    setMode(
      { formLogin, formRegister, authTitle, authSub, writeState },
      mode,
      persist
    );
  }

  function validateLoginForm() {
    const okUsername = validateUsername(loginUsername, loginUsernameError);
    const okPassword = validatePassword(loginPassword, loginPasswordError);
    return okUsername && okPassword;
  }

  function validateRegisterForm() {
    const okUsername = validateUsername(registerUsername, registerUsernameError);
    const okEmail = validateEmail(registerEmail, registerEmailError);
    const okPassword = validatePassword(registerPassword, registerPasswordError);
    const okConfirm = validateConfirmPassword(
      registerPassword,
      registerConfirm,
      registerConfirmError
    );

    return okUsername && okEmail && okPassword && okConfirm;
  }

  bindTextInput(loginUsername, "loginUsername", writeState);
  bindTextInput(registerUsername, "registerUsername", writeState);
  bindTextInput(registerEmail, "registerEmail", writeState);

  bindPasswordToggle();

  bindSwitchLinks({
    loginPath,
    registerPath,
    writeState,
  });

  if (loginUsername) loginUsername.addEventListener("input", validateLoginForm);
  if (loginPassword) loginPassword.addEventListener("input", validateLoginForm);

  if (registerUsername) registerUsername.addEventListener("input", validateRegisterForm);
  if (registerEmail) registerEmail.addEventListener("input", validateRegisterForm);
  if (registerPassword) registerPassword.addEventListener("input", validateRegisterForm);
  if (registerConfirm) registerConfirm.addEventListener("input", validateRegisterForm);

  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      if (!validateLoginForm()) {
        e.preventDefault();
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", function (e) {
      if (!validateRegisterForm()) {
        e.preventDefault();
      }
    });
  }

  restoreState({
    readState,
    setModeFn: setActiveMode,
    formLogin,
    formRegister,
    loginUsername,
    registerUsername,
    registerEmail,
  });
});