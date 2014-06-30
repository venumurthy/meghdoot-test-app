
describe("Home Page", function() {
  it("should display the correct title", function () {
    browser.get('/#');
    expect(browser.getTitle()).toBe('Meghdoot - Test App');
  });
});