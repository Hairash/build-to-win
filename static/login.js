document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.getElementById('login-form');
  loginForm.addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(loginForm);
    fetch('/login', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        console.log(data);
        const messageBox = document.getElementById('login-message');

        if (data.success) {
          messageBox.textContent = 'Login successful!';
          messageBox.className = 'message-box success';
          messageBox.style.display = 'block';
          setTimeout(() => {
            window.location.href = '/game';
          }, 1000);
        } else {
          messageBox.textContent = 'Login failed: ' + data.error;
          messageBox.className = 'message-box error';
          messageBox.style.display = 'block';
        }
      })
      .catch(error => console.error('Error:', error));
  });

  const registrationForm = document.getElementById('registration-form');
  registrationForm.addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(registrationForm);
    fetch('/register', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        console.log(data);
        const messageBox = document.getElementById('login-message');

        if (data.success) {
          messageBox.textContent = 'Registered successfully!';
          messageBox.className = 'message-box success';
          messageBox.style.display = 'block';
        } else {
          messageBox.textContent = 'Register failed: ' + data.error;
          messageBox.className = 'message-box error';
          messageBox.style.display = 'block';
        }
      })
      .catch(error => console.error('Error:', error));
  });
});
