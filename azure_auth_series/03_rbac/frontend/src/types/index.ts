export interface GraphUserProfile {
  displayName: string;
  givenName: string;
  surname: string;
  userPrincipalName: string;
  mail: string | null;
  id: string;
  jobTitle: string | null;
  officeLocation: string | null;
  mobilePhone: string | null;
  businessPhones: string[];
}
