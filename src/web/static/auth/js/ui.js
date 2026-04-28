export function setMode(
  { formLogin, formRegister, authTitle, authSub, writeState },
  mode,
  persist = false
) {
  const isRegister = mode === "register";

  if (formLogin) formLogin.classList.toggle("active", !isRegister);
  if (formRegister) formRegister.classList.toggle("active", isRegister);

  if (authTitle) authTitle.textContent = isRegister ? "Create account" : "Welcome back";
  if (authSub) {
    authSub.textContent = isRegister
      ? "Free forever — no credit card needed"
      : "Sign in to your monitoring dashboard";
  }

  if (persist && writeState) {
    writeState({ activeForm: isRegister ? "register" : "login" });
  }
}

export function restoreState({
  readState,
  setModeFn,
  formLogin,
  formRegister,
  loginUsername,
  registerUsername,
  registerEmail,
}) {
  const state = readState();
  setModeFn(state.activeForm, false);

  if (state.loginUsername && loginUsername && !loginUsername.value) {
    loginUsername.value = state.loginUsername;
  }

  if (state.registerUsername && registerUsername && !registerUsername.value) {
    registerUsername.value = state.registerUsername;
  }

  if (state.registerEmail && registerEmail && !registerEmail.value) {
    registerEmail.value = state.registerEmail;
  }

  const firstInput =
    state.activeForm === "register"
      ? formRegister && formRegister.querySelector("input:not([type='hidden'])")
      : formLogin && formLogin.querySelector("input:not([type='hidden'])");

  if (firstInput) firstInput.focus();
}

export function bindTextInput(node, key, writeState) {
  if (!node) return;

  node.addEventListener("input", function () {
    writeState({ [key]: node.value });
  });
}

export function bindPasswordToggle() {
  document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = btn.dataset.target;
      const input = document.getElementById(targetId);
      const eyeOpen = btn.querySelector(".eye-open");
      const eyeClosed = btn.querySelector(".eye-closed");

      if (!input) return;

      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";

      if (eyeOpen) eyeOpen.style.display = isHidden ? "none" : "block";
      if (eyeClosed) eyeClosed.style.display = isHidden ? "block" : "none";
      btn.setAttribute("aria-pressed", isHidden ? "true" : "false");
    });
  });
}

export function bindSwitchLinks({ loginPath, registerPath, writeState }) {
  document.querySelectorAll(".switch-link").forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();

      const mode = link.dataset.mode === "register" ? "register" : "login";
      writeState({ activeForm: mode });

      window.location.assign(mode === "register" ? registerPath : loginPath);
    });
  });
}