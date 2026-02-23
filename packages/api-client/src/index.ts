/**
 * eco-base API Client — public exports.
 * URI: eco-base://packages/api-client
 */
export { EcoApiClient } from './client';
export type {
  ClientConfig, RetryConfig, RequestInterceptor,
  RequestConfig, ApiResponse, ApiError,
} from './client';
