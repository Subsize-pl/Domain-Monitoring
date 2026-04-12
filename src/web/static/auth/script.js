document.addEventListener("DOMContentLoaded", function () {
  const formLogin    = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const authTitle    = document.getElementById("auth-title");
  const authSub      = document.getElementById("auth-sub");

  document.querySelectorAll(".switch-link").forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const mode = link.dataset.mode; //  "login" | "register"

      if (mode === "register") {
        if (formLogin) formLogin.classList.remove("active");
        if (formRegister) formRegister.classList.add("active");
        if (authTitle) authTitle.textContent = "Create account";
        if (authSub) authSub.textContent = "Free forever — no credit card needed";
        const first = formRegister && formRegister.querySelector("input");
        if (first) first.focus();
      } else {
        if (formRegister) formRegister.classList.remove("active");
        if (formLogin) formLogin.classList.add("active");
        if (authTitle) authTitle.textContent = "Welcome back";
        if (authSub) authSub.textContent = "Sign in to your monitoring dashboard";
        const first = formLogin && formLogin.querySelector("input");
        if (first) first.focus();
      }
    });
  });

  document.querySelectorAll(".eye-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = btn.getAttribute("data-target");
      const input    = document.getElementById(targetId);
      const eyeOpen  = btn.querySelector(".eye-open");
      const eyeClosed = btn.querySelector(".eye-closed");

      if (!input) return;

      if (input.type === "password") {
        input.type = "text";
        if (eyeOpen) eyeOpen.style.display = "none";
        if (eyeClosed) eyeClosed.style.display = "block";
        btn.setAttribute("aria-pressed", "true");
      } else {
        input.type = "password";
        if (eyeOpen) eyeOpen.style.display = "block";
        if (eyeClosed) eyeClosed.style.display = "none";
        btn.setAttribute("aria-pressed", "false");
      }
    });
  });

  const regForm    = document.getElementById("reg-form");
  const regPass    = document.getElementById("reg-password");
  const regConfirm = document.getElementById("reg-confirm");
  const confirmErr = document.getElementById("confirm-error");

  function checkPasswordMatch() {
    if (!regPass || !regConfirm || !confirmErr) return;

    if (regConfirm.value === "") {
      confirmErr.textContent = "";
      regConfirm.classList.remove("error");
      return;
    }
    if (regPass.value !== regConfirm.value) {
      confirmErr.textContent = "Passwords do not match";
      regConfirm.classList.add("error");
    } else {
      confirmErr.textContent = "";
      regConfirm.classList.remove("error");
    }
  }

  if (regConfirm && regPass) {
    regConfirm.addEventListener("input", checkPasswordMatch);
    regPass.addEventListener("input", checkPasswordMatch);
  }

  if (regForm) {
    regForm.addEventListener("submit", function (e) {
      if (!regPass || !regConfirm || regPass.value !== regConfirm.value) {
        e.preventDefault();
        if (confirmErr) confirmErr.textContent = "Passwords do not match";
        if (regConfirm) {
          regConfirm.classList.add("error");
          regConfirm.focus();
        }
      }
    });
  }

});