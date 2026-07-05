package org.jaltediye.cereqon.data.remote

import okhttp3.HttpUrl
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Rewrites outgoing Retrofit requests to use the current [ServerUrlStore] base URL.
 */
@Singleton
class DynamicBaseUrlInterceptor @Inject constructor(
    private val serverUrlStore: ServerUrlStore,
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val configuredBase = serverUrlStore.asHttpUrl()
        val originalUrl = original.url

        val rebuiltUrl = originalUrl.newBuilder()
            .scheme(configuredBase.scheme)
            .host(configuredBase.host)
            .port(configuredBase.port)
            .build()

        val rebuiltRequest = original.newBuilder()
            .url(rebuiltUrl)
            .build()

        return chain.proceed(rebuiltRequest)
    }
}
