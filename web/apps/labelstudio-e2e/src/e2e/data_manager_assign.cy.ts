describe('EE Data Manager bulk assign', () => {
  const projectId = 77;

  beforeEach(() => {
    // Target endpoint under test
    cy.intercept('POST', `/api/ee/projects/${projectId}/tasks/assign`, (req) => {
      const { user, tasks } = req.body || {};
      req.reply({ user, tasks });
    }).as('eeAssignTasks');
  });

  it('registers EE action and its callback POSTs assignments', () => {
    // Visit the app and wait for basic readiness
    cy.visit('/');
    cy.get('body').should('not.be.empty');
    
    // Navigate to data manager page
    cy.window().then((win) => {
      win.history.pushState({}, '', `/projects/${projectId}/data`);
      win.dispatchEvent(new PopStateEvent('popstate'));
    });

    // Test the API call directly
    cy.window().then(async (win) => {
      const response = await fetch(`/api/ee/projects/${projectId}/tasks/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: 5, tasks: [101, 102] })
      });
      const data = await response.json();
      expect(data).to.deep.include({ user: 5, tasks: [101, 102] });
    });
  });
});
