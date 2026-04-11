import { createClient } from "contentful";

export const contentfulClient = createClient({
  space:
    process.env.NEXT_PUBLIC_CONTENTFUL_SPACE_ID || "gismnhbb3kki",
  accessToken:
    process.env.NEXT_PUBLIC_CONTENTFUL_ACCESS_TOKEN ||
    "e7if3JoufyZzs33-q8zqwSxvgCKsNdLu3eRwuiJaocM",
});
