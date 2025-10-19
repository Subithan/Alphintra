import { ApolloClient, InMemoryCache, createHttpLink, from, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';
import { getToken, removeToken } from '@/lib/auth';
import { buildGatewayUrl, buildGatewayWsUrl } from './config/gateway';

// HTTP Link for queries and mutations
const httpLink = createHttpLink({
  uri: buildGatewayUrl('/graphql'),
});

// WebSocket Link for subscriptions
const wsLink = typeof window !== 'undefined' ? new GraphQLWsLink(
  createClient({
    url: buildGatewayWsUrl('/graphql'),
    connectionParams: () => {
      const token = getToken();
      return {
        authorization: token ? `Bearer ${token}` : '',
      };
    },
  })
) : null;

// Auth Link to add authorization header
const authLink = setContext((_, { headers }) => {
  const token = getToken();
  
  return {
    headers: {
      ...headers,
      Authorization: token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
  };
});

// Error Link to handle authentication errors
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path, extensions }) => {
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
      );
      
      // DEVELOPMENT: Disable authentication error redirects
      // Uncomment the lines below to re-enable auth error handling for production
      // Handle authentication errors
      // if (extensions?.code === 'UNAUTHENTICATED' || extensions?.code === 'FORBIDDEN') {
      //   removeToken();
      //   // Redirect to login page
      //   if (typeof window !== 'undefined') {
      //     window.location.href = '/login';
      //   }
      // }
    });
  }
  
  if (networkError) {
    console.error(`[Network error]: ${networkError}`);
    
    // DEVELOPMENT: Disable authentication error redirects
    // Uncomment the lines below to re-enable auth error handling for production
    // Handle network authentication errors
    // if ('statusCode' in networkError && (networkError.statusCode === 401 || networkError.statusCode === 403)) {
    //   removeToken();
    //   if (typeof window !== 'undefined') {
    //     window.location.href = '/login';
    //   }
    // }
  }
});

// Split link to direct subscriptions to WebSocket and queries/mutations to HTTP
const splitLink = typeof window !== 'undefined' && wsLink
  ? split(
      ({ query }) => {
        const definition = getMainDefinition(query);
        return (
          definition.kind === 'OperationDefinition' &&
          definition.operation === 'subscription'
        );
      },
      wsLink,
      authLink.concat(httpLink)
    )
  : authLink.concat(httpLink);

// Apollo Client configuration
export const apolloClient = new ApolloClient({
  link: from([errorLink, splitLink]),
  cache: new InMemoryCache({
    typePolicies: {
      User: {
        fields: {
          portfolio: {
            merge: true,
          },
        },
      },
      Strategy: {
        fields: {
          backtestResults: {
            merge(existing = [], incoming: any[]) {
              return [...existing, ...incoming];
            },
          },
        },
      },
      Query: {
        fields: {
          marketData: {
            keyArgs: ['symbol', 'timeframe'],
            merge(existing, incoming) {
              return incoming;
            },
          },
          strategies: {
            keyArgs: ['filter', 'sort'],
            merge(existing = { edges: [] }, incoming) {
              return {
                ...incoming,
                edges: [...existing.edges, ...incoming.edges],
              };
            },
          },
          marketplaceStrategies: {
            keyArgs: ['filter', 'sort'],
            merge(existing = { edges: [] }, incoming) {
              return {
                ...incoming,
                edges: [...existing.edges, ...incoming.edges],
              };
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
      notifyOnNetworkStatusChange: true,
    },
    query: {
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
  connectToDevTools: process.env.NODE_ENV === 'development',
});

// Helper function to refetch all active queries
export const refetchAllQueries = () => {
  return apolloClient.refetchQueries({
    include: 'active',
  });
};

// Helper function to clear cache
export const clearCache = () => {
  return apolloClient.clearStore();
};
