/** Authentication domain types */

export interface AuthToken {
  accessToken: string
  tokenType: string
  expiresIn: number
}

export interface TokenValidation {
  isValid: boolean
  message?: string
}

/** Decoded JWT payload — matches what the backend encodes */
export interface JwtPayload {
  sub: string        // username
  user_id: number
  email: string
  exp: number
  iat?: number
  is_staff?: boolean
  is_superuser?: boolean
}
