// Theme toggle functionality.
const themeToggle = document.querySelector('.theme-toggle');
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

// Get theme from localStorage or system preference.
const currentTheme = localStorage.getItem('theme') ||
  (prefersDarkScheme.matches ? 'dark' : 'light');

// Apply theme on load.
document.documentElement.setAttribute('data-theme', currentTheme);

const sunIcon = `
<svg width="24" height="24" fill="white" stroke="white" stroke-width="2" viewBox="0 0 24 24" color="black">
  <circle cx="12" cy="12" r="5"></circle>
  <path d="M12 1v2"></path>
  <path d="M12 21v2"></path>
  <path d="M4.22 4.22l1.42 1.42"></path>
  <path d="M18.36 18.36l1.42 1.42"></path>
  <path d="M1 12h2"></path>
  <path d="M21 12h2"></path>
  <path d="M4.22 19.78l1.42-1.42"></path>
  <path d="M18.36 5.64l1.42-1.42"></path>
</svg>
`;

const moonIcon = `
<svg width="24" height="24" fill="#333" stroke="#333" stroke-width="2" viewBox="0 0 24 24">
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
</svg>
`;

themeToggle.innerHTML = currentTheme === 'dark' ? sunIcon : moonIcon;

// Toggle theme.
themeToggle.addEventListener('click', () => {
  const newTheme = document.documentElement.getAttribute('data-theme') === 'dark'
    ? 'light'
    : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  themeToggle.innerHTML = newTheme === 'dark' ? sunIcon : moonIcon;
});
