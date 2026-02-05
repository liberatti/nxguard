import packageJson from '../package.json';

export const environment = {
  name: packageJson.name,
  production: false,
  appContext: "/nxg",
  apiUrl: `http://127.0.0.1:5000/nxg`,
  apiDateFormat: "YYYY-MM-DDTHH:mm:ss.SSS[Z]",
  version: packageJson.version + "-dev"
};