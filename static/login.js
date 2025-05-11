document.addEventListener('DOMContentLoaded', function() {
  const registrationForm = document.getElementById('login-form');
  registrationForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(registrationForm);
    fetch('/login', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        console.log(data);
        if (data.success) {
          alert('Login successful!');
          // TODO: redirect to the game page
        } else {
          alert('Login failed: ' + data.message);
        }
      })
      .catch(error => console.error('Error:', error));
  });
});
