export interface Referral {
  information: string
  contact: string
  contactDetails: string
}

// This repository is public. Add contact details only with the contact's consent.
export const referrals: Referral[] = [
  {
    information: '抖音电商履约相关业务，招 28 届后端实习生，base 北京。\n组内 Leader 非常 nice，会帮你 landing。有合适人选可以联系我。',
    contact: '我借此火',
    contactDetails: 'QQ：1421085859'
  }
]
