import request from './request'

export interface Doctor {
  id: number
  full_name: string
  department: string | null
}

export function getDoctors(department?: string) {
  return request.get<Doctor[]>('/api/users/doctors', {
    params: department ? { department } : undefined,
  })
}
