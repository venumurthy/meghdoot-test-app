exports.config = {
  
  seleniumAddress: 'http://localhost:46037/wd/hub',
  
  capabilities: {
    browserName: 'phantomjs',
    version: '',
    platform: 'ANY'
  },
  
  specs: [
    './e2e/**/*.spec.js'
  ],

  baseUrl: 'http://localhost:3000'
};
