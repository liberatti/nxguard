import packageJson from '../package.json';

const appContext = "/nxg";

export const environment = {
  name: packageJson.name,
  production: true,
  appContext,
  apiUrl: `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ''}${appContext}`,
  apiDateFormat: "YYYY-MM-DDTHH:mm:ss.SSS[Z]",
  version: packageJson.version
};