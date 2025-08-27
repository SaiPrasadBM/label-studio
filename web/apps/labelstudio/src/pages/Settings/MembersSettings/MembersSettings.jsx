import { useState } from "react";
import { Button, Space, Section, SectionTitle, FormRow, FormGroup, Alert, ToastType } from "@humansignal/ui";
import { useAPI } from "../../../providers/ApiProvider";
import { useProject } from "../../../providers/ProjectProvider";

export const MembersSettings = () => {
  const { project } = useProject();
  const { callApi } = useAPI();
  const [addIds, setAddIds] = useState("");
  const [removeIds, setRemoveIds] = useState("");
  const [enableIds, setEnableIds] = useState("");
  const [disableIds, setDisableIds] = useState("");
  const [message, setMessage] = useState(null);

  const parseIds = (value) =>
    value
      .split(/[,\s]+/)
      .map((v) => v.trim())
      .filter(Boolean)
      .map((v) => Number(v))
      .filter((v) => Number.isFinite(v));

  const onAssign = async () => {
    const add = parseIds(addIds);
    const remove = parseIds(removeIds);

    const res = await callApi("eeProjectMembersAssign", {
      params: { pk: project.id },
      body: { add, remove },
    });
    if (res && !res.error) setMessage({ type: "success", text: `Added: ${res.added?.join(", ") || "-"}; Removed: ${res.removed?.join(", ") || "-"}` });
  };

  const onEnable = async () => {
    const enable = parseIds(enableIds);
    const disable = parseIds(disableIds);

    const res = await callApi("eeProjectMembersEnable", {
      params: { pk: project.id },
      body: { enable, disable },
    });
    if (res && !res.error) setMessage({ type: "success", text: `Enabled: ${res.enabled?.join(", ") || "-"}; Disabled: ${res.disabled?.join(", ") || "-"}` });
  };

  return (
    <Section>
      <SectionTitle>Project Members</SectionTitle>
      {message && (
        <Alert type={message.type === "success" ? ToastType.success : ToastType.error}>{message.text}</Alert>
      )}
      <Space direction="vertical" size="large">
        <FormGroup>
          <FormRow title="Add user IDs">
            <input
              placeholder="e.g. 12, 15, 18"
              value={addIds}
              onChange={(e) => setAddIds(e.target.value)}
            />
          </FormRow>
          <FormRow title="Remove user IDs">
            <input
              placeholder="e.g. 21 22 23"
              value={removeIds}
              onChange={(e) => setRemoveIds(e.target.value)}
            />
          </FormRow>
          <Button onClick={onAssign}>Apply Add/Remove</Button>
        </FormGroup>

        <FormGroup>
          <FormRow title="Enable user IDs">
            <input
              placeholder="e.g. 12, 15"
              value={enableIds}
              onChange={(e) => setEnableIds(e.target.value)}
            />
          </FormRow>
          <FormRow title="Disable user IDs">
            <input
              placeholder="e.g. 16 17"
              value={disableIds}
              onChange={(e) => setDisableIds(e.target.value)}
            />
          </FormRow>
          <Button onClick={onEnable}>Apply Enable/Disable</Button>
        </FormGroup>
      </Space>
    </Section>
  );
};

MembersSettings.title = "Members";
MembersSettings.path = "/settings/members";
