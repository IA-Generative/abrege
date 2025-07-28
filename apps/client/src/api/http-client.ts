import axios from 'axios'

function createHttpClient (baseURL: string) {
  const client = axios.create({
    baseURL,
    withCredentials: false,
    headers: {
      Accept: 'application/json',
    },
  })
  return client
}

export default createHttpClient
