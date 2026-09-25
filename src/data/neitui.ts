import initialReferrals from './neitui.json'

export interface Referral {
  id: string
  information: string
  contact: string
  contactDetails: string
  createdAt: string
}

// This public seed is also used to initialize the server database.
export const referrals: Referral[] = initialReferrals
