// Docs: https://www.instantdb.com/docs/modeling-data

import { i } from "@instantdb/admin";

const _schema = i.schema({
  // We inferred 1 attribute!
  // Take a look at this schema, and if everything looks good,
  // run `push schema` again to enforce the types.
  entities: {
    $files: i.entity({
      path: i.string().unique().indexed(),
      url: i.any(),
    }),
    $users: i.entity({
      email: i.string().unique().indexed(),
    }),
    bunnies: i.entity({
      data: i.string(),
      name: i.string(),
    }),
    messages: i.entity({
      content: i.string(),
      role: i.string(),
      createdAt: i.number(),
    }),
  },
  links: {},
  rooms: {},
});

// This helps Typescript display nicer intellisense
type _AppSchema = typeof _schema;
interface AppSchema extends _AppSchema { }
const schema: AppSchema = _schema;

export type { AppSchema };
export default schema;
