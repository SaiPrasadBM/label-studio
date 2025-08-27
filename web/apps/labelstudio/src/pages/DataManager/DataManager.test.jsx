import React from "react";
import { render, waitFor } from "@testing-library/react";
import { ToastContext, ToastType } from "@humansignal/ui";

// Mock dynamic imports used by DataManagerPage
jest.mock("@humansignal/datamanager", () => ({}), { virtual: true });
jest.mock("@humansignal/editor", () => ({}), { virtual: true });

// Mock routing
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useHistory: () => ({ push: jest.fn() }),
  generatePath: (tpl, params) => tpl.replace(":id", params.id),
}));

// Mock LS Providers
jest.mock("../../providers/ApiProvider", () => ({
  useAPI: () => ({
    callApi: jest.fn().mockResolvedValue([]), // mlBackends -> []
    handleError: jest.fn(),
  }),
}));

jest.mock("../../providers/ProjectProvider", () => ({
  useProject: () => ({ project: { id: 77, expert_instruction: null, show_instruction: false } }),
}));

jest.mock("../../providers/RoutesProvider", () => ({
  useParams: () => ({ id: 77 }),
  useContextProps: () => jest.fn(),
}));

// Minimal Block component CSS deps are irrelevant in unit env
jest.mock("../../components/Modal/Modal", () => ({ modal: jest.fn() }));

// Mock ../../components to avoid importing App/Sentry tree
jest.mock("../../components", () => ({
  Spinner: () => <div data-testid="spinner" />,
}));

// After mocks are set up, require the component under test
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { DataManagerPage } = require("./DataManager");

const createDMInstance = (overrides = {}) => {
  const handlers = {};

  return {
    on: jest.fn((event, cb) => {
      handlers[event] = cb;
    }),
    off: jest.fn(),
    updateActions: jest.fn(),
    destroy: jest.fn(),
    store: {
      currentView: {
        reload: jest.fn().mockResolvedValue(undefined),
        clearSelection: jest.fn(),
      },
      fetchProject: jest.fn(),
    },
    lsf: { task: { id: 1 } },
    ...overrides,
    __handlers: handlers,
  };
};

describe("DataManagerPage EE Assign action", () => {
  const toast = { show: jest.fn() };

  beforeEach(() => {
    jest.resetAllMocks();
    // Ensure globals expected by DataManager initializer exist
    global.window.LabelStudio = {};
    global.window.APP_SETTINGS = { hostname: "http://localhost:8080", editor_keymap: {} };
    // Mock DataManager constructor
    const instance = createDMInstance();
    global.window.DataManager = jest.fn().mockImplementation(() => instance);
    // Mock fetch
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    // Mock prompt
    jest.spyOn(window, "prompt").mockReturnValue("5");
  });

  test("registers EE action and invokes callback to POST assign", async () => {
    render(
      <ToastContext.Provider value={toast}>
        <DataManagerPage />
      </ToastContext.Provider>,
    );

    // Wait for DataManager initialization and action registration
    await waitFor(() => {
      expect(window.DataManager).toHaveBeenCalled();
    });

    const dmInstance = window.DataManager.mock.results[0].value;

    await waitFor(() => {
      expect(dmInstance.updateActions).toHaveBeenCalled();
    });

    // Get registered action tuple
    const [[actionDef, actionCb]] = dmInstance.updateActions.mock.calls[0][0];

    expect(actionDef.id).toBe("ee_assign_tasks");

    // Invoke the callback with a selection
    await actionCb({ included: [101, 102], all: false });

    expect(fetch).toHaveBeenCalledWith("/api/ee/projects/77/tasks/assign", expect.objectContaining({
      method: "POST",
    }));

    // Expect success toast
    expect(toast.show).toHaveBeenCalledWith(expect.objectContaining({ type: ToastType.success }));

    // Expect store updates
    expect(dmInstance.store.currentView.reload).toHaveBeenCalled();
    expect(dmInstance.store.fetchProject).toHaveBeenCalled();
    expect(dmInstance.store.currentView.clearSelection).toHaveBeenCalled();
  });
});
