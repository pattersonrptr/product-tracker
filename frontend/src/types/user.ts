/** User domain types */

export interface User {
  id: string
  username: string
  email: string
  isActive: boolean
  isStaff: boolean
  isSuperuser: boolean
  createdAt?: string
  updatedAt?: string
}
