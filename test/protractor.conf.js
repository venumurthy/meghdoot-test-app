exports.config = {
  
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
