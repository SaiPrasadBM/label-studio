import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MembersSettings } from "./MembersSettings";

// Provide minimal stubs for UI components used inside MembersSettings
jest.mock("@humansignal/ui", () => ({
  Button: (props) => <button {...props} />,
  Input: (props) => <input {...props} />,
  Space: ({ children }) => <div>{children}</div>,
  Section: ({ children }) => <section>{children}</section>,
  SectionTitle: ({ children }) => <h2>{children}</h2>,
  FormRow: ({ children, title }) => (
    <div>
      {title && <label>{title}</label>}
      {children}
    </div>
  ),
  FormGroup: ({ children }) => <div>{children}</div>,
  Alert: ({ children }) => <div>{children}</div>,
  ToastType: { success: "success", error: "error", info: "info", warning: "warning" },
}));

jest.mock("../../../providers/ApiProvider", () => ({
  useAPI: () => ({
    callApi: jest.fn().mockResolvedValue({ added: [12], removed: [21], enabled: [12], disabled: [16] }),
  }),
}));

jest.mock("../../../providers/ProjectProvider", () => ({
  useProject: () => ({ project: { id: 10 } }),
}));

// UI components already tested separately; here we focus on wiring

describe("MembersSettings", () => {
  test("calls eeProjectMembersAssign and shows success message", async () => {
    render(<MembersSettings />);

    const addInput = screen.getByPlaceholderText(/e.g. 12, 15, 18/i);
    const removeInput = screen.getByPlaceholderText(/e.g. 21 22 23/i);

    fireEvent.change(addInput, { target: { value: "12, 15" } });
    fireEvent.change(removeInput, { target: { value: "21" } });

    fireEvent.click(screen.getByText(/Apply Add\/Remove/i));

    await waitFor(() => expect(screen.getByText(/Added:/i)).toBeTruthy());
  });

  test("calls eeProjectMembersEnable and shows success message", async () => {
    render(<MembersSettings />);

    const enableInput = screen.getByPlaceholderText("e.g. 12, 15");
    const disableInput = screen.getByPlaceholderText(/e.g. 16 17/i);

    fireEvent.change(enableInput, { target: { value: "12" } });
    fireEvent.change(disableInput, { target: { value: "16" } });

    fireEvent.click(screen.getByText(/Apply Enable\/Disable/i));

    await waitFor(() => expect(screen.getByText(/Enabled:/i)).toBeTruthy());
  });
});
