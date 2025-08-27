import { SidebarMenu } from "../../components/SidebarMenu/SidebarMenu";
import { WebhookPage } from "../WebhookPage/WebhookPage";
import { DangerZone } from "./DangerZone";
import { MembersSettings } from "./MembersSettings/MembersSettings";
import { GeneralSettings } from "./GeneralSettings";
import { AnnotationSettings } from "./AnnotationSettings";
import { LabelingSettings } from "./LabelingSettings";
import { MachineLearningSettings } from "./MachineLearningSettings/MachineLearningSettings";
import { PredictionsSettings } from "./PredictionsSettings/PredictionsSettings";
import { StorageSettings } from "./StorageSettings/StorageSettings";
import { isInLicense, LF_CLOUD_STORAGE_FOR_MANAGERS } from "../../utils/license-flags";
import { Assignments } from "./Assignments/Assignments";
import "./settings.scss";
import { useCurrentUser } from "../../providers/CurrentUser";

const isAllowCloudStorage = !isInLicense(LF_CLOUD_STORAGE_FOR_MANAGERS);

export const MenuLayout = ({ children, ...routeProps }) => {
  const { user } = useCurrentUser();
  // Derive capabilities from org role
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { getCapabilities } = require("../../utils/capabilities");
  const caps = getCapabilities(user?.org_role, user?.fine_role, user?.coarse_role);
  const isOwnerOrMaintainer = ["OWNER", "MAINTAINER"].includes((user?.org_role || "").toUpperCase());

  const items = [
    GeneralSettings,
    LabelingSettings,
    AnnotationSettings,
    // Admin-only sections
    caps.can_manage_jobs && MachineLearningSettings,
    caps.can_assign_jobs_tasks_projects && MembersSettings,
    PredictionsSettings,
    caps.can_manage_storages && isAllowCloudStorage && StorageSettings,
    caps.can_manage_jobs && WebhookPage,
    caps.can_manage_jobs && DangerZone,
    isOwnerOrMaintainer && Assignments,
  ].filter(Boolean);

  return (
    <SidebarMenu
      menuItems={items}
      path={routeProps.match.url}
      children={children}
    />
  );
};

const pages = {
  AnnotationSettings,
  LabelingSettings,
  MachineLearningSettings,
  MembersSettings,
  PredictionsSettings,
  WebhookPage,
  DangerZone,
  Assignments,
};

isAllowCloudStorage && (pages.StorageSettings = StorageSettings);

export const SettingsPage = {
  title: "Settings",
  path: "/settings",
  exact: true,
  layout: MenuLayout,
  component: GeneralSettings,
  pages,
};
