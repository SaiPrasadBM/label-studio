import { SidebarMenu } from "../../components/SidebarMenu/SidebarMenu";
import { WebhookPage } from "../WebhookPage/WebhookPage";
import { DangerZone } from "./DangerZone";
import { GeneralSettings } from "./GeneralSettings";
import { AnnotationSettings } from "./AnnotationSettings";
import { LabelingSettings } from "./LabelingSettings";
import { MachineLearningSettings } from "./MachineLearningSettings/MachineLearningSettings";
import { PredictionsSettings } from "./PredictionsSettings/PredictionsSettings";
import { StorageSettings } from "./StorageSettings/StorageSettings";
import { isInLicense, LF_CLOUD_STORAGE_FOR_MANAGERS } from "../../utils/license-flags";
import "./settings.scss";
import { useCurrentUser } from "../../providers/CurrentUser";

const isAllowCloudStorage = !isInLicense(LF_CLOUD_STORAGE_FOR_MANAGERS);

export const MenuLayout = ({ children, ...routeProps }) => {
  const { user } = useCurrentUser();
  const isEditor = user?.fine_role === 'EDITOR';

  const items = [
    GeneralSettings,
    LabelingSettings,
    AnnotationSettings,
    // Admin-only sections
    isEditor && MachineLearningSettings,
    PredictionsSettings,
    isEditor && isAllowCloudStorage && StorageSettings,
    isEditor && WebhookPage,
    isEditor && DangerZone,
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
  PredictionsSettings,
  WebhookPage,
  DangerZone,
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
