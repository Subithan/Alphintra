import { ApolloClient, InMemoryCache, createHttpLink, split, from, ApolloLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';
import { setContext } from '@apollo/client/link/context';
import { buildGatewayUrl, buildGatewayWsUrl } from '../config/gateway';

// HTTP Link for queries and mutations
const httpLink = createHttpLink({
  uri: buildGatewayUrl('/graphql'),
});

// WebSocket Link for subscriptions
const wsLink = typeof window !== 'undefined' ? new GraphQLWsLink(createClient({
  url: buildGatewayWsUrl('/graphql'),
  connectionParams: () => {
    const token = localStorage.getItem('auth_token');
    return {
      authorization: token ? `Bearer ${token}` : '',
    };
  },
})) : null;

// Authentication Link
const authLink = setContext((_, { headers }) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    }
  };
});

// Error Link for handling GraphQL errors
const errorLink = new ApolloLink((operation, forward) => {
  return forward(operation).map(result => {
    if (result.errors) {
      console.error('GraphQL Errors:', result.errors);
      // Handle specific error types
      result.errors.forEach(error => {
        if (error.extensions?.code === 'UNAUTHENTICATED') {
          // Handle authentication errors
          console.error('Authentication error:', error.message);
          // Could redirect to login or refresh token
        }
      });
    }
    return result;
  });
});

// Split link to route queries/mutations to HTTP and subscriptions to WebSocket
const splitLink = wsLink ? split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink,
) : httpLink;

// Create Apollo Client
export const apolloClient = new ApolloClient({
  link: from([
    errorLink,
    authLink,
    splitLink,
  ]),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          workflows: {
            keyArgs: ['filters'],
            merge(existing, incoming, { args }) {
              if (!args?.filters?.skip || args.filters.skip === 0) {
                // If no skip or skip is 0, replace the cache
                return incoming;
              }
              // Otherwise, merge the results (for pagination)
              return {
                ...incoming,
                workflows: [
                  ...(existing?.workflows || []),
                  ...incoming.workflows,
                ],
              };
            },
          },
          executions: {
            keyArgs: ['workflowId', 'filters'],
            merge(existing, incoming, { args }) {
              if (!args?.filters?.skip || args.filters.skip === 0) {
                return incoming;
              }
              return {
                ...incoming,
                executions: [
                  ...(existing?.executions || []),
                  ...incoming.executions,
                ],
              };
            },
          },
        },
      },
      Workflow: {
        fields: {
          workflow_data: {
            merge: true, // Deep merge workflow data
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
  },
});

// Helper function to set auth token
export const setAuthToken = (token: string | null) => {
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }
};

// Helper function to get auth token
export const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

// Helper function to clear cache
export const clearCache = () => {
  apolloClient.cache.reset();
};

export default apolloClient;
