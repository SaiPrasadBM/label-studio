import { SidebarMenu } from "../../components/SidebarMenu/SidebarMenu";
import { PeoplePage } from "./PeoplePage/PeoplePage";
import { WebhookPage } from "../WebhookPage/WebhookPage";
import { RequireRole } from "../../components/Auth/RequireRole";

const ALLOW_ORGANIZATION_WEBHOOKS = window.APP_SETTINGS.flags?.allow_organization_webhooks;

const MenuLayout = ({ children, ...routeProps }) => {
  const menuItems = [PeoplePage];

  if (ALLOW_ORGANIZATION_WEBHOOKS) {
    menuItems.push(WebhookPage);
  }
  return (
    <RequireRole fineRole="EDITOR">
      <SidebarMenu menuItems={menuItems} path={routeProps.match.url} children={children} />
    </RequireRole>
  );
};

const organizationPages = {};

if (ALLOW_ORGANIZATION_WEBHOOKS) {
  organizationPages[WebhookPage] = WebhookPage;
}

export const OrganizationPage = {
  title: "Organization",
  path: "/organization",
  exact: true,
  layout: MenuLayout,
  component: PeoplePage,
  pages: organizationPages,
};
