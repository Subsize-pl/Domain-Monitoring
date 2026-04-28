import {
  EMAIL_PATTERN,
  MIN_PASSWORD_LENGTH,
  MIN_USERNAME_LENGTH,
} from "./rules.js";

import {
    MESSAGES,
} from "./messages.js"

export function ensureErrorNode(input, id) {
  if (!input) return null;

  const existing = document.getElementById(id);
  if (existing) return existing;

  const errorNode = document.createElement("span");
  errorNode.className = "field-error";
  errorNode.id = id;

  const inputGroup = input.closest(".input-group");
  const inputWrap = input.closest(".input-wrap");

  if (inputGroup && inputWrap && inputWrap.parentElement === inputGroup) {
    inputWrap.insertAdjacentElement("afterend", errorNode);
  } else if (inputGroup) {
    inputGroup.appendChild(errorNode);
  } else {
    input.insertAdjacentElement("afterend", errorNode);
  }

  return errorNode;
}

export function setFieldState(input, errorNode, message) {
  if (!input) return true;

  const valid = !message;
  input.classList.toggle("error", !valid);
  input.toggleAttribute("aria-invalid", !valid);

  if (errorNode) {
    errorNode.textContent = message || "";
  }

  return valid;
}

export function validateRequiredText(input, errorNode, label, minLength = 1) {
  const value = (input?.value || "").trim();

  if (!value) {
    return setFieldState(input, errorNode, `${label} is required`);
  }

  if (value.length < minLength) {
    return setFieldState(
      input,
      errorNode,
      `${label} must be at least ${minLength} characters`
    );
  }

  return setFieldState(input, errorNode, "");
}

export function validateUsername(input, errorNode) {
  return validateRequiredText(input, errorNode, "Username", MIN_USERNAME_LENGTH);
}

export function validateEmail(input, errorNode) {
  const value = (input?.value || "").trim();

  if (!value) {
    return setFieldState(input, errorNode, MESSAGES.emailRequired);
  }

  if (!EMAIL_PATTERN.test(value)) {
    return setFieldState(input, errorNode, MESSAGES.emailInvalid);
  }

  return setFieldState(input, errorNode, "");
}

export function validatePassword(input, errorNode) {
  const value = input?.value || "";

  if (!value) {
    return setFieldState(input, errorNode, MESSAGES.passwordRequired);
  }

  if (value.length < MIN_PASSWORD_LENGTH) {
    return setFieldState(
      input,
      errorNode,
      MESSAGES.passwordTooShort(MIN_PASSWORD_LENGTH)
    );
  }

  return setFieldState(input, errorNode, "");
}

export function validateConfirmPassword(passwordInput, confirmInput, errorNode) {
  const passwordValue = passwordInput?.value || "";
  const confirmValue = confirmInput?.value || "";

  if (!confirmValue) {
    return setFieldState(confirmInput, errorNode, MESSAGES.confirmRequired);
  }

  if (passwordValue !== confirmValue) {
    return setFieldState(confirmInput, errorNode, MESSAGES.passwordsMismatch);
  }

  return setFieldState(confirmInput, errorNode, "");
}