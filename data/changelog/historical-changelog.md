> ## Documentation Index
> Fetch the complete documentation index at: https://developers.notion.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Historical changelog

> View an archive of Notion Developers updates prior to September 2023

export const developerConnectionsUrl = "https://app.notion.com/developers/connections";

<Note>
  **View the current [Changelog](/page/changelog) for the newest updates.**

  This page is a historical archive of updates older than September 2023. This is kept separate from the current changelog to keep page navigation faster while retaining older updates.
</Note>

<Update label="August 23 - September 5, 2023">
  * The [Working with databases guide](/guides/data-apis/working-with-databases) was revised to improve its readability and to make additional resources easier to find.
  * Notion's [Postman collection](https://www.postman.com/notionhq/notion-s-api-workspace/collection/52041987-03f70d8f-b6e5-4306-805c-f95f7cdf05b9) for the API was updated. Be sure to pull recent changes into your forked version.
  * A reminder was added to the [Comments endpoints](/reference/create-a-comment) to update [integration capabilities](/reference/capabilities) for comments prior to using the endpoints. (Read/write comment capabilities are off by default and can be turned on in the <a href={developerConnectionsUrl}>integration dashboard</a>.)
  * General clean-up and improvements, including code formatting.
</Update>

<Update label="August 8 - August 22, 2023">
  * The [Build your first integration](/guides/get-started/quick-start) guide was rewritten with new demo code to help developers learn how to use Notion’s API even faster.
    * A new [sample app](https://github.com/makenotion/notion-cookbook/tree/main/examples/javascript/web-form-with-express) was added to the [Notion SDK for JavaScript](https://github.com/makenotion/notion-sdk-js) `/examples` directory. This completed sample app is referenced in the new [Build your first integration](/guides/get-started/quick-start) guide.
  * The description for the `block_id` path parameter was updated for the [Append block children](/reference/patch-block-children) endpoint to indicate that a block ID or page ID can be used.
  * A clarification was added to [documentation](/reference/retrieve-a-database) for retrieving/updating database properties: If a property is based on a relation to another database, the related database also needs to be shared with the integration.
  * A clarification was added to documentation for [querying databases](/reference/post-database-query-filter#multi-select). When filtering a multi-select property, the `contains` field will filter for exact matches for the string provided.
  * The [Working with comments](/guides/data-apis/working-with-comments) guide was updated with additional examples to distinguish between creating page comments and inline discussion comments.
    * The [Create a comment](/reference/create-a-comment) endpoint description now links to the Working with comments guide to help developers find additional resources faster.
  * If you haven’t already, join our [Notion Devs Slack group](https://join.slack.com/t/notiondevs/shared_invite/zt-3u9oid9q8-HLUBmMVWYK~g9HFo4U4raA) to learn from other developers building with the public API.

  ### Notice for an upcoming Public API change

  #### We will soon be rolling out changes to the Formulas property (Formulas 2.0), and as such, we will be making a change to the Notion Public API.

  This is a non-versioned change and is expected to be in effect in the next couple weeks.

  **tl;dr:** As part of the Formulas 2.0 rollout, the Public API’s format of the string value for [`formula.expression`](/reference/property-object#formula) will be changing. Public API calls with formula inputs in the old format will still succeed. On write operations, the old format will be supported indefinitely, but on read, only the new format will be returned. This change is being made to improve the formulas experience and ensure parity with the Notion app.

  No action is required for creating or updating database formulas. Reading database [`formula.expression`](/reference/property-object#formula) values may require developer changes.

  #### What do you need to know?

  **The string value of `formula.expression` is changing; the schema is not.**

  * **On write** via the Public API ([create](/reference/create-a-database) or [update](/reference/update-a-database) database endpoints), Notion will support using the old format as a Public API input in the formula property schema indefinitely *and* will support writing in the **new** format.
  * Database objects returned via the Public API will have the new formulas 2.0 format.

  <CodeGroup>
    ```javascript javascript expandable theme={null}
    // Old format
    "Updated price": {
      "id": "YU%7C%40",
      "name": "Updated price",
      "type": "formula",
      "formula": {
        "expression": "prop(\"Price\") * 2"
      }
    }

    // New format (upcoming)
    "Updated price": {
      "id": "YU%7C%40",
      "name": "Updated price",
      "type": "formula",
      "formula": {
          "expression": "{{notion:block_property:BtVS:00000000-0000-0000-0000-000000000000:8994905a-074a-415f-9bcf-d1f8b4fa38e4}}/2"
      }
    }
    ```
  </CodeGroup>

  #### Why is this happening?

  Notion databases allow you to build a fully customizable system for you and your team – they provide a place where you can keep all your information in one place, with the ability to build views, filters, and workflows that can be adapted to your needs.

  The formula property helps you take that even further – allowing you to perform calculations, create specialized views, and provide an extra layer of insight based on information in other database properties. It helps expand what you can do in Notion databases.

  We are improving the formulas experience so that:

  1. It’s easier to write formulas.
  2. Formula outputs look and feel more native to Notion.
  3. The formula language can fulfill more specific needs.

  Changes being made to the API are to ensure parity with the Notion app.

  #### What do you need to do?

  This is a non-versioned change that will not affect most developers. As mentioned, the formula property format will still have the same schema in the Public API; only the value of the `formula.expression` field will change.

  Keep an eye on this changelog for when the update becomes available in the Public API.
</Update>

<Update label="July 25 - August 7, 2023">
  * Notion is excited to announce our [Technology Partnership Program](https://www.notion.so/technology-partner-program). 🎉 This program is open to companies who have built a public integration and are interested in improving and scaling their integration with Notion’s support. If you think your integration and company could be a fit, [learn more and apply here](https://www.notion.so/technology-partner-program).

  * We’ve updated our API reference docs to include information on Notion’s [wiki databases and verified pages](https://www.notion.so/help/wikis-and-verified-pages). Updates include:

    * An overview on wikis in the guide to [working with databases](/guides/data-apis/working-with-databases#database-properties).
    * The [`verification`](/reference/page-property-values#verification) page property was added to the [Page properties](/reference/page-property-values) documentation.
    * The [Create a database](/reference/create-a-database) and [Query a database](/reference/post-database-query) endpoint documentation was updated to reflect API changes related to wikis. Namely, that querying wiki databases can return both [Page](/reference/page) and [Database](/reference/database) objects.

  * The [Error codes](/reference/status-codes#error-codes) section in the [Status code](/reference/status-codes) page was updated to include examples of the `"message"` returned with each type of API error, as well as descriptions of the issue each error code represents.

  * A number of sample cURL commands in our docs were still using an old [Notion Version](/reference/versioning) in their headers. These have all been updated.

  * A clarification was added to the [Authorization guide](/guides/get-started/authorization#making-api-requests-with-an-internal-connection) that the [Notion Version](/reference/versioning) is always required in public API request headers.
</Update>

<Update label="July 11 - July 24, 2023">
  * A new integration [example](https://github.com/makenotion/notion-cookbook/tree/main/examples/javascript/parse-text-from-any-block-type) was added to the Notion SDK for JavaScript repo. This example shows how to get the plain text from any block type currently supported by the public API.
  * The new unique ID page property was added to the [Page properties](/reference/page-property-values) documentation. When used, the unique ID (`unique_id`) auto-increments for every new page created in a database. An optional prefix can be included that will be applied to the ID values.

  <Frame caption="The unique ID in a Notion page's properties">
    <img src="https://mintcdn.com/notion-demo/9OFhQspLr8njnajd/images/docs/c599280-unique_id.png?fit=max&auto=format&n=9OFhQspLr8njnajd&q=85&s=92437cad7aa45d267c0f0a3d82874be2" width="1066" height="498" data-path="images/docs/c599280-unique_id.png" />
  </Frame>

  * Workspace Owners can now see *all* internal integrations created in a workspace via the <a href={developerConnectionsUrl}>integration dashboard</a>. This includes integrations created by themselves and other Workspace Owners. We’ve included this information in our [Getting Started](/guides/get-started/overview#connection-types) guide.
  * A [Notion SDK for JavaScript](https://github.com/makenotion/notion-sdk-js) code sample was added to the [Create a database](/reference/create-a-database) endpoint documentation.
</Update>

<Update label="June 13 - July 10, 2023">
  * We updated our [Getting started guide](/guides/get-started/overview) to help developers who are new to the public API better understand how the API relates to integrations.
  * The [Block object](/reference/block#embed) docs were updated with a tip on how to embed Vimeo links in a Notion page via the API.
  * A new `after` parameter has been added to the [Append block children](/reference/patch-block-children) endpoint. Developers can now specific where to append a new block, instead of appending it to the end of a parent block by default.
      <CodeGroup>
        ```bash cURL theme={null}
        curl -X PATCH https://api.notion.com/v1/blocks/16d8004e-5f6a-42a6-9811-51c22ddada12/children \
          -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
          -H "Content-Type: application/json" \
          -H "Notion-Version: 2022-06-28" \
          --data '{
            "children": [
            ...
            }
          ], after: "<block_id_to_append_after>"
        }'
        ```
      </CodeGroup>
  * The [Authorization guide](/guides/get-started/authorization) had a clarification added to help developers find the resources they need for Link Preview integrations.
  * The new `public_url` property was added to the docs. When a page or database has been shared publicly, the response body will include a `public_url` value.
      <CodeGroup>
        ```json JSON theme={null}
        {
          "object": "page",
          "id": "<id>",
          "created_time": "2023-06-02T19:54:00.000Z",
          "last_edited_time": "2023-06-02T23:04:00.000Z",
          "created_by": { ... },
          "last_edited_by": { ... },
          "cover": null,
          "icon": null,
          "parent": { ... },
          "archived": false,
          "properties": { ... },
          "url": "<url>",
          "public_url": "<public-url>"
        }
        ```
      </CodeGroup>
  * The [Retrieve block children](/reference/get-block-children) endpoint documentation was updated to help developers who are new to the public API better understand the endpoint’s functionality.
  * The [Retrieve a block](/reference/retrieve-a-block) endpoint documentation was updated with some additional information related to working with page content.
  * The `invalid_grant` code was added to our [Status codes](/reference/status-codes) documentation. This code is returned when the authorization grant (e.g. token) provided is invalid. For example, a status code `400` with an `invalid_grant` code will be returned when the token provided has expired.
  * The [Rich text](/reference/rich-text) documentation was updated with additional information on what rich text is and how the Notion uses it.
</Update>

<Update label="May 30 - June 12, 2023">
  * Our guides and docs related to Link Preview integrations have been updated to help developers find the information they need faster. Improvements have been made to the following guides and API reference docs:

    * [Getting started guide](/guides/get-started/overview)
    * [Introduction to Link Previews guide](/guides/link-previews/introduction)
    * Link Preview integration guide
    * [Unfurl attribute object docs](/reference/unfurl-attribute-object)

  * We added more information about the `plain_text` property found in the `rich_text` object. Learn more about rich text in our [Rich text object](/reference/rich-text) docs.

  * The docs related to [filtering](/reference/post-database-query-filter) and [sorting](/reference/post-database-query-sort) database queries now have more code examples for developers building integrations with the [Notion SDK for JavaScript](https://github.com/makenotion/notion-sdk-js).

  * We reorganized the REST API reference navigation bar after removing the “Other” section to make its child pages easier to find.
</Update>

<Update label="May 16 - May 29, 2023">
  * The [Query a database](/reference/post-database-query) and [Filter database entries](/reference/post-database-query-filter) docs were updated with additional code examples of passing single and multiple filters.
  * The [Working with comments](/guides/data-apis/working-with-comments) guide was updated to clarify how to retrieve and add comments using the REST API.
  * The references docs for `rollup` [page properties](/reference/page-property-values#rollup), as well as the [Retrieve a page property](/reference/retrieve-a-page-property) and [Retrieve a page](/reference/retrieve-a-page) endpoints were updated with additional information related to limitations. In cases where a page property — like a rollup — has more than 25 references, the [Retrieve a page property](/reference/retrieve-a-page-property) endpoint must be used to receive a complete response.
  * An outdated Changelog URL now redirects to this Changelog page to help avoid confusion.
</Update>

<Update label="May 2 - May 15, 2023">
  * We added a database schema size recommendation of **50KB** to our docs to help developers manage their database query performance. It is strongly recommended that developers keep their schema size under this number.
  * The [Update a database](/reference/update-a-database) page was updated to improve readability. Additional information on how this endpoint differs from related endpoints was also added to help developers better navigate the REST API docs.
  * The [Query a database](/reference/post-database-query#errors) page was updated with additional information about the `filter_properties` query parameter. When used with the REST API, this query parameter is passed as a string, like so:

  ```
  https://api.notion.com/v1/databases/[database_id]/query?filter_properties=[property_id_1]&filter_properties=[property_id_2]
  ```

  When used with the [JavaScript SDK](https://github.com/makenotion/notion-sdk-js), the `filter_properties` option accepts an array of property ID strings:

  <CodeGroup>
    ```javascript JavaScript theme={null}
    notion.databases.query({
    	database_id: 'databaseID',
    	filter_properties: ["propertyID1", "propertyID2"]
    })
    ```
  </CodeGroup>

  * Docs that mention the `redirect_uri` — a value used with [public integrations](/guides/get-started/public-integrations) — were updated to clarify when this value is required. Refer to the [Create a token](/reference/create-a-token) page for a complete description.
  * The video block-type was updated on the [Block Object](/reference/block#video) page to clarify accepted video types. YouTube URLs that contain `watch` or `embed` are supported video types.
  * The [Append a block](/reference/patch-block-children) page content was reorganized to improve readability.
</Update>

<Update label="April 18 - May 1, 2023">
  * Link Preview integration docs were updated to reflect a change regarding how link previews are enabled in the <a href={developerConnectionsUrl}>integration dashboard</a>.
  * The [versioning page](/reference/versioning) was updated to clarify that the `Notion-Version` header is required in Notion REST API requests.
  * The [parent object page](/reference/parent-object) and API reference docs for [database POST requests](/reference/create-a-database) and [blocks PATCH requests](/reference/patch-block-children) were updated to better explain how parenting rules work.
  * The [Integration guide](/guides/get-started/quick-start) was updated with more links to help developers find resources faster.
  * Number database properties now support the Peruvian sol as a currency format. To use it, set `"peruvian_sol"` as the value for a number’s `format` field when creating or updating a database property or [schema](/reference/property-schema-object#number-configuration).
  * General docs housekeeping, such reducing the number of callouts in our API reference docs to improve the readability.
</Update>

<Update label="March 14 - April 17, 2023">
  * Our developer community Slack invite link was updated. [Join here](https://join.slack.com/t/notiondevs/shared_invite/zt-3u9oid9q8-HLUBmMVWYK~g9HFo4U4raA) to connect with other developers building with the Notion API.
  * The [Authorization guide](/guides/get-started/authorization) was updated to include more information on creating integrations, adding templates to public integrations, and more code examples to get you started, faster.
  * We’ve added more code examples to our API reference docs, including [Archive a page](/reference/archive-a-page) and [Authentication](/reference/authentication).
  * General docs housekeeping, such reducing the number of callouts in our API reference docs to improve the readability.
</Update>

<Update label="February 28 - March 13, 2023">
  We don’t have any changes to announce this week! Stay tuned, and in the meantime check out our platform roadmap for a look at what we’re building.
</Update>

<Update label="February 14 - 27, 2023">
  ### Fixes and improvements

  * You can now update [rollup database properties](/reference/property-object#rollup) via the API. To programmatically update a `rollup` property, send a PATCH to [Update a database](/reference/update-a-database) that specifies the change in the `properties` body param.
</Update>

<Update label="January 31 - February 13, 2023">
  We don’t have any updates to share right now. Stay tuned for the next changelog! To get a sense for what we’re heads down working on, check out the [platform roadmap](/page/changelog).
</Update>

<Update label="January 18 - 30, 2023">
  ### Fixes and improvements

  * Stay tuned!

  ### New things

  * Added a token `Refresh` button to the settings page for internal integrations. Click `Refresh` to generate a new token for your internal integration.

  <Frame caption="You can now refresh an internal integration token from the integration settings page.">
    <img src="https://mintcdn.com/notion-demo/SXcROsTox2NhPn9o/images/docs/b1d6c0c-2023-01-13_10.58.16.gif?s=2a2a1e3671c7b1fec00590b7aba51afd" width="1055" height="1104" data-path="images/docs/b1d6c0c-2023-01-13_10.58.16.gif" />
  </Frame>
</Update>

<Update label="January 3 - 17, 2023">
  ### New things

  * Shipped detailed docs for Link Previews including an [overview](/guides/link-previews/introduction) and [reference materials](/reference/unfurl-attribute-object).
</Update>

<Update label="December 19, 2022 - January 2, 2023">
  ### Fixes and improvements

  * The [Retrieve a Page endpoint](/reference/retrieve-a-page#errors) can now return specific page property values when you include the `filter_properties` path param.
  * You can now request specific page property values from a database by passing `filter_properties` in the request body to the [Query a database endpoint](/reference/post-database-query).

  ### New things

  * Happy 2023! For a sneak peek of what we’ll be up to this year, check out our updated [platform roadmap](/page/changelog).
</Update>

<Update label="December 6 - 18, 2022">
  ### Fixes and improvements

  * Updated the [Append block children](/reference/patch-block-children) and [Retrieve block children](/reference/get-block-children) endpoints to specific supported block types to create a more consistent dev experience. The endpoints now throw an error if the block type in the request does not [support children](/reference/block#block-types-that-support-child-blocks).

  ### New things

  * Built a ✨Glitch ✨ demo that updates Notion tasks when a linked GitHub PR is closed or merged. [Give it a spin!](https://glitch.com/~notion-task-github-pr-sync)
</Update>

<Update label="November 22 - December 5, 2022">
  We took advantage of the US Thanksgiving holiday to host a mini internal hackathon.

  Nothing to share from that, yet! It’s been a quiet few weeks.

  If you want something to read while you stay tuned for the next update, check out the revised [Get started](/guides/get-started/overview) guide.
</Update>

<Update label="November 8 - 21, 2022">
  * We added a `this_week` filter for database queries. You can now search for database entries where the `"date"`, `"created_time"`, or `"last_edited_time"` property value falls within the current week. Refer to the [date filter condition](/reference/post-database-query-filter#date) docs for details.
</Update>

<Update label="October 25 - November 7, 2022">
  * Number database properties now support the Singapore dollar as a currency format. To use it, set `"singapore_dollar"` as the value for a number’s `format` field when creating or updating a database [property](/reference/property-object#number) or [schema](/reference/property-schema-object#number-configuration).
</Update>

<Update label="October 11 - 24, 2022">
  * You can now add a Notion template option to a public integration from the <a href={developerConnectionsUrl}>integration's settings page</a>. For details on what the permissions flow looks like for users who opt in to the template, refer to the [Authorization guide](/guides/get-started/authorization).
</Update>

<Update label="September 26 - October 10, 2022">
  * A [`relation`](/reference/property-value-object#relation-property-values) property value now includes a `has_more` property when returned by the [Retrieve a page endpoint](/reference/retrieve-a-page). `has_more` is `true` if the `relation` has more than 25 page references. Otherwise, `has_more` is `false`.
  * We added a `workspace_name` property to [bot user objects](/reference/user#bots). If the bot  `owner.type` is `"workspace"`, then `workspace.name` identifies the name of the workspace that owns the bot. If the `owner.type` is `"user"`, then `workspace.name` is `null`.
</Update>

<Update label="September 12 - 25, 2022">
  Started an experiment to improve [search endpoint](/reference/post-search) performance by tweaking how we call Elasticsearch under the hood.
</Update>

<Update label="August 29 - September 11, 2022">
  * Fixed a bug where date mentions ended in a `→` character even if they only represented a single date, not a date range.
  * Added an `Authorization URL` field to the public integration form. You can now click to copy the URL that allows users to authorize your integration (read more in the [Authorization guide](/guides/get-started/authorization)).
  * Corrected an error that caused the [`getProperty` endpoint](/reference/retrieve-a-page-property) to return only one item if the `property_id` belonged to a multi-item [`Files`](/reference/property-item-object#files) page property.
</Update>

<Update label="August 31, 2022">
  ### Version 2022-06-28 includes page property types and values

  Responses for page retrievals, database queries, and searches will again include page property types and values. This matches the behavior in version `2022-02-22` and takes effect on August 31, 2022.
</Update>

<Update label="August 15 - 28, 2022">
  ### Features

  * The public API now supports the following functionality for `status` properties:

    * Reading and updating `status` properties on pages ([read more](/reference/property-value-object#status-property-values))
    * Reading, but not updating, `status` property configuration on databases ([read more](/reference/property-object#status))
    * Filtering or sorting by `status` properties when querying databases ([read more](/reference/post-database-query-filter#status))

  * `header_1`, `header_2`, and `header_3` blocks now have an `is_toggleable` property, to better indicate whether they are heading toggle blocks. ([read more](/reference/block#headings))

    * Headings can be togglified and un-togglified by setting `is_toggleable` to true or false, but note that all the children inside the toggle must be removed before it can be untogglified.
</Update>

<Update label="August 1 - 14, 2022">
  No updates for these past two weeks, but stay tuned for the next changelog!
</Update>

<Update label="July 18 - July 31, 2022">
  ### Features

  * Added support for [reading](/reference/list-comments) and [writing](/reference/create-a-comment) page-level comments in the API.
</Update>

<Update label="July 19, 2022">
  ### Comments API

  Today we're launching a brand new set of APIs for interacting with Notion comments. This includes the ability to:

  * Read comments from a page or block.
  * Add a comment to a page.
  * Add a comment to an existing discussion thread on a block.

  For more information, check out the new [guide](/guides/data-apis/working-with-comments) or dive straight into the [API reference](/reference/create-a-comment).
</Update>

<Update label="July 5 - 17, 2022">
  ### Features

  * Released a new version of the API, `2022-06-28`. Previous versions of the API are still supported. Read more about the new version [here](/changelog/releasing-notion-version-2022-06-28).
  * Created a new template repository for getting started with the Notion API and the official SDK. [Find it here.](https://github.com/makenotion/notion-sdk-typescript-starter)

  ### Bug fixes and performance improvements

  * Exported many more named types for API response objects in the [official SDK](https://github.com/makenotion/notion-sdk-js).
  * Fixed a bug in the official SDK where some API requests would not work due a capitalization issue. (This was a community-submitted PR; thank you @dvanoni!)
</Update>

<Update label="July 6, 2022">
  ### Releasing Notion-Version 2022-06-28

  **Update from August 31, 2022**: Page properties can now be retrieved using the page, query database, and search endpoints, in addition to the page properties endpoint.

  Today we’re releasing Notion-Version `2022-06-28` with the following backwards incompatible changes:

  * Page properties must be retrieved using the page properties endpoint.
  * Parents are now always direct parents; a parent field has been added to block.
  * Database relations have a type of `single_property` and `dual_property`.

  Read more about each of these changes below.

  ### Page properties must be retrieved using the page properties endpoint

  Previously, the [page object](/reference/page) returned from page endpoints, as well as the query database and search endpoint, returned a `properties` field that contained all the page’s properties along with its value:

  <CodeGroup>
    ```json Previous Version Response theme={null}
    "properties": {
        "Name": {
          "id": "title",
          "type": "title",
          "title": [
            {
              "type": "text",
              "text": {
                "content": "Avocado",
                "link": null
              },
              "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
              },
              "plain_text": "Avocado",
              "href": null
            }
          ]
       }
    }
    ```
  </CodeGroup>

  While convenient, returning accurate results for all properties resulted in bad performance and timeouts for larger databases or pages with lots of mentions. To combat performance, on March 1st, we [added a disclaimer](/reference/property-value-object) that page objects stopped returning accurate results for pages with more than 25 mentions to other objects (which affected properties of type `title`, `rich_text`, `relation`, `people`, `rollup`, and `formula`).

  In October 2021, [we introduced](/changelog/retrieve-page-property-values) a way to more accurately retrieve individual page properties via the [retrieve a page property item endpoint](/reference/retrieve-a-page-property). With this endpoint, we’re able to paginate complex properties that involve additional look-ups.

  With version `2022-06-28`, the `type` and `property` value from page objects are removed. Thus moving forward, all property value retrieval must happen through the retrieve a page property item endpoint.

  <CodeGroup>
    ```json New Version Response theme={null}
    "properties": {
        "Name": {
          "id": "title"
       }
    }
    ```
  </CodeGroup>

  For more examples of how to use the retrieve a page property item endpoint, our [SDK examples](/page/examples) have been updated to use the retrieve a page property item endpoint.

  For more details about why page properties are so complex, we wrote about it in our [“Creating the Notion API”](https://www.notion.so/blog/creating-the-notion-api) blog post.

  ### Parents are now always direct parents; a parent field has been added to block

  Previously, when accessing the parent of a database or page, that parent was always either a page, database, or workspace. This is un-faithful to the actual data model of Notion, where the parent may also be another block; for example, you can nest a page under a toggle block.

  The parent field for page and database has been changed so that it is now always the direct parent of that page or database, and a new parent type has been added: `block_id`.

  Additionally, a `parent` field has been added to the block object. Together, these changes allow you to fully traverse Notion’s tree.

  To emulate the previous behavior of retrieving the page, database, or space parent, you may traverse up the tree using the retrieve a block endpoint. If the parent ≠ one of those types, retrieve the parent block until it is.

  Read more about parent types [here](/reference/parent-object).

  ### Database relations have a type of `single_property` and `dual_property`

  Relation properties in databases objects now have a type of `single_property` or `dual_property`. These can be used to create one way relations between databases as well as two way relations within a database.

  ### New version of the JavaScript SDK

  Coinciding with all of these changes, we've released a new major version (v2.0.0) of the [Notion JavaScript SDK](https://github.com/makenotion/notion-sdk-js). To upgrade to this new version, run `npm install @notionhq/client@latest` or `yarn upgrade --latest @notionhq/client` from within your repository.
</Update>

<Update label="June 20 - July 4, 2022">
  ### Features

  * Added limited readonly support for database status properties. Read more about status properties [here](https://www.notion.so/help/guides/status-property-gives-clarity-on-tasks).

    * Status property values are returned in the [Retrieve a page](/reference/retrieve-a-page) endpoint. See [Property values](/reference/property-value-object) for more information.
    * Status property configuration is not supported yet. See [Property object](/reference/property-object) for more information.

  ### Bug Fixes

  * Added a validation for adding new rollup properties that prevents creating a rollup of another rollup.
</Update>

<Update label="June 6 - June 19, 2022">
  ### Features

  * Added support for creating inline databases with `is_inline`. Read more [here](/reference/database).
  * Added support for reading and writing database descriptions with the `description` field. Read more [here](/reference/database).
</Update>

<Update label="May 23 - June 5, 2022">
  ### Bug fixes and performance improvements

  * The public API once again supports inline`mailto` links in rich text.
</Update>

<Update label="May 9 - 22, 2022">
  ### Bug fixes and performance improvements

  * We now validate URLs used to create inline text links in the public API. For more details on inline links in rich text, see the [Rich text object](/reference/rich-text) documentation.
  * The [Search](/reference/post-search) endpoint now returns fuzzier matches, including plurals and different verb tenses. This corresponds to fuzzier matches while searching in the Notion app and should result in more search results overall for any given query.
  * Fixed a bug where the integration page at <a href={developerConnectionsUrl}>integrations dashboard</a> wouldn't load.
</Update>

<Update label="May 10, 2022">
  ### Link Preview APIs

  Today we’re excited to launch a new set of APIs for Link Preview integrations. Over the past six months, we launched link previews with tools like Slack, Trello, Figma, and Asana, allowing users to preview authenticated content in a new structured block.

  We built link previews to make it easy for users to easily share information in one place using a link. But with a regular link, the information would become automatically stale, making it difficult to share the latest updates among teams. Link previews let supported services share authenticated, up-to-date content inside Notion.

  Learn more about link previews [here](/page/link-previews-api).
</Update>

<Update label="April 25 - May 9, 2022">
  ### Bug fixes and performance improvements

  * We've shipped a couple of improvements under the hood to make the search and query database endpoints faster. We're actively looking into 500s and timeouts on the query database endpoint in particular.
  * Fixed a bug in the OAuth page picker where Shared pages wouldn't load until the workspace switcher was clicked
</Update>

<Update label="April 11 - 24, 2022">
  ### Bug fixes and performance improvements

  * Fixed a bug where some rollups and relations appeared empty when they shouldn't have.
  * Fixed a bug in the query database endpoint where an invalid pagination cursor was being returned.
</Update>

<Update label="March 28 - April 10, 2022">
  There was a [company-wide product bug bash](https://www.notion.so/releases)! As a result nothing API-specific to share for these 2 weeks, but we've been hard at work improving test coverage and paring down tech debt.
</Update>

<Update label="March 14 - 27, 2022">
  ### Features

  * You can now filter databases on the created at and last edited at timestamps, even if they don't have a corresponding property of that type. Read more [here](/reference/post-database-query-filter#timestamp).
  * A [`Retry-After`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After) response header is now being sent with rate limited request responses. The value of this field is set as an integer number of seconds (in decimal). Requests made after waiting this minimum amount of time should not be rate limited. Read more about our rate limits [here](/reference/request-limits#rate-limits).

  ### Bug fixes and performance improvements

  * Stopped throwing an error when rendering property formulas that hadn't been set up yet in the [Retrieve a page property item](/reference/retrieve-a-page-property) endpoint. These formulas now return `null` values.
</Update>

<Update label="March 18, 2022">
  ### Query a database endpoint supports filtering by timestamp

  When [querying a database](/reference/post-database-query) using filters, you previously were only able to build filters using properties that were explicitly defined in the database schema. We've added a new type of filter for the created timestamp and last edited timestamp of any page within the database. This means you can filter by these attributes, even if the database doesn't have a "Created time" or "Last edited time" *property*.

  You can read more about this filter type [here](/reference/post-database-query-filter#timestamp), but as a preview here is how you would filter by the created timestamp:

  <CodeGroup>
    ```json JSON theme={null}
    {
        "filter": {
            "timestamp": "created_time",
            "created_time": {
              "past_week": {}
            }
        }
    }
    ```
  </CodeGroup>

  And here's how you would filter by the last edited time:

  <CodeGroup>
    ```json JSON theme={null}
    {
        "filter": {
            "timestamp": "last_edited_time",
            "last_edited_time": {
              "after": "2021-05-10"
            }
        }
    }
    ```
  </CodeGroup>

  Note that you can also use this filter type within a compound filter.
</Update>

<Update label="February 28, 2022 - March 13, 2022">
  ### Features

  * Block colors are now supported in the API! Read more about it [here](/changelog/block-colors-are-now-supported-in-the-api).

  ### Bug fixes and performance improvements

  * Rich text objects now properly include template mentions. Read more about this type of text object [here](/reference/rich-text#template-mention-type-object).
</Update>

<Update label="March 8, 2022">
  ### Block colors are now supported in the API

  We have added support for block colors in the Notion Public API. There is now a `color` keyword for the following block types: `paragraph`, `heading_1`, `heading_2`, `heading_3`, `bulleted_list_item`, `numbered_list_item`, `to_do`, `toggle`, `callout`, `quote`, and `table_of_contents`. For these block types, the block color is returned in the [block object](/reference/block), and you can use the [update block](/reference/update-a-block), [append block children](/reference/patch-block-children), and [create page](/reference/post-page) endpoints to update the color of existing blocks and create new blocks with color.

  The colors supported are `default`, `gray`, `brown`, `orange`, `yellow`, `green`, `blue`, `purple`, `pink`, `red`, `gray_background`, `brown_background`, `orange_background`, `yellow_background`, `green_background`, `blue_background`, `purple_background`, `pink_background`, and `red_background`.

  <CodeGroup>
    ```json Example Block expandable theme={null}
    {
        "object": "block",
        "id": "79bc0ae2-b002-4ecd-92db-870354734aaf",
        "created_time": "2022-03-03T22:49:00.000Z",
        "last_edited_time": "2022-03-03T22:49:00.000Z",
        "created_by": {
            "object": "user",
            "id": "914ff1b3-45c7-48dc-b2c2-be37d21e7695"
        },
        "last_edited_by": {
            "object": "user",
            "id": "914ff1b3-45c7-48dc-b2c2-be37d21e7695"
        },
        "has_children": false,
        "archived": false,
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": "This block has color!",
                        "link": null
                    },
                    "annotations": {
                        "bold": false,
                        "italic": false,
                        "strikethrough": false,
                        "underline": false,
                        "code": false,
                        "color": "default"
                    },
                    "plain_text": "This block has color!",
                    "href": null
                }
            ],
            "icon": {
                "type": "emoji",
                "emoji": "💡"
            },
            "color": "green_background"
        }
    }
    ```
  </CodeGroup>
</Update>

<Update label="March 7, 2022">
  ### Updated Developers Terms

  With the API officially out of beta, Notion has updated our developer terms of service as of March 1st, 2022. View our updated terms [here](https://www.notion.so/notion/Developer-Terms-ba4131408d0844e08330da2cbb225c20).
</Update>

<Update label="February 14, 2022 - 28, 2022: Block by Block edition!">
  <Note>
    **The API is officially out of beta!**

    Read more about it [here](https://www.notion.so/blog/api-ga).
  </Note>

  ### Features

  * We now have a [roadmap](/page/changelog), so you have a better sense of what we'll be building next.
  * We released a new version of the API, `2022-02-22`. This version makes our requests and responses more consistent across properties, blocks, and filters, and officially deprecates the list databases endpoint. Read more [here](/changelog/releasing-notion-version-2022-02-22).
  * We now show the public API status independently of Notion's status on [https://status.notion.so/](https://status.notion.so/).
  * Added `created_by` and `edited_by` to pages, blocks, and databases, and added `archived` to databases. Read more [here](/changelog/created-by-and-last-edited-by-properties-in-block-page-and-database-objects).
  * Added new ways for admins of Enterprise workspaces to view and control the integrations installed in their workspaces. Read more [here](https://www.notion.so/help/add-and-manage-integrations-with-the-api).
  * Added more information to paginated responses to make it easier to fetch complete responses for complex property types. Read more [here](/reference/pagination).

  ### Bug fixes and performance improvements

  * Fixed a bug where pages and databases with archived (i.e. trashed) ancestors would show `archived: false`. They now show `archived: true` because they are, in fact, archived.
  * Improved API performance when rendering users who are members in the space. This affects all user, block, and page-related endpoints since users can be mentioned in both page properties and rich text.
  * Added a message about sharing relevant pages and databases with a bot in the 404 not found error message. We found that this was one of the more common reasons for API users to get a 404 when calling the API.
  * Fixed a bug where bots could be given a more restrictive "Can edit content" access on child databases, which prevented some bots with write access from being able to update the database schema.
  * Fixed a bug where user mentions failed with "user not found" when creating new blocks, even if those users should have been visible to the bot.
  * Fixed a bug where malformed properties in a single page would cause an entire request to the query database endpoint to fail.
  * Fixed a bug where it was possible to update a page/database in the trash. Attempting to update a trashed page or database now returns a validation error.
  * Fixed a bug in the get page property endpoint where retrieving a rollup property which referenced a relation containing pages the bot did not have access to skipped those pages and returned an incorrect result. We now return a validation error.
  * Fixed a bug in the get page property endpoint where retrieving a formula property whose depth exceeds what we can compute in the API simply returned the wrong value. We now return a validation error.
</Update>

<Update label="March 1, 2022">
  ### Created by and last edited by properties in Block, Page and Database objects

  We have added `created_by` and `last_edited_by` properties for [block](/reference/block), [page](/reference/page) and [database objects](/reference/database) corresponding to the users who have created or last edited these objects. Both properties are [user objects](/reference/user) which will contain `object` and `id` keys. This is a backwards compatible change that is available in older versions of the API as well.

  <CodeGroup>
    ```json Example page object expandable theme={null}
    {
      "object": "page",
      "id": "e722caec-ae02-4a41-9bbd-286f65f8dca4",
      "created_time": "2022-02-15T21:24:00.000Z",
      "last_edited_time": "2022-02-17T22:40:00.000Z",
      "created_by": {
        "object": "user",
        "id": "71e95936-2737-4e11-b03d-f174f6f13087"
      },
      "last_edited_by": {
        "object": "user",
        "id": "5ba97cc9-e5e0-4363-b33a-1d80a635577f"
      },
      "cover": null,
      "icon": null,
      "parent": {
        "type": "page_id",
        "page_id": "a7e32210-c151-4b96-8b94-ea659b1e8e4f"
      },
      "archived": false,
      "properties": {
        "title": {
          "id": "title",
          "type": "title",
          "title": [
            {
              "type": "text",
              "text": {
                "content": "Tasks",
                "link": null
              },
              "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
              },
              "plain_text": "Tasks",
              "href": null
            }
          ]
        }
      },
      "url": "https://notion.so/Tasks-e722caecae024a419bbd286f65f8dca4"
    }
    ```

    ```json Example block object expandable theme={null}
    {
      "object": "block",
      "id": "9bc30ad4-9373-46a5-84ab-0a7845ee52e6",
      "created_time": "2021-03-16T16:31:00.000Z",
      "created_by": {
        "object": "user",
        "id": "cb38e95d-00cf-4e7e-adce-974f4a44a547"
    	},
      "last_edited_time": "2021-03-16T16:32:00.000Z",
      "last_edited_by": {
        "object": "user",
        "id": "e79a0b74-3aba-4149-9f74-0bb5791a6ee6"
    	},
      "has_children": false,
      "type": "to_do",
      "archived": false,
      "to_do": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Lacinato kale",
              "link": null
            },
            "annotations": {
              "bold": false,
              "italic": false,
              "strikethrough": false,
              "underline": false,
              "code": false,
              "color": "default"
            },
            "plain_text": "Lacinato kale",
            "href": null
          }
        ],
        "checked": false
      }
    }
    ```

    ```json Example database object expandable theme={null}
    {
      "object": "database",
      "id": "e8d49c2d-9644-4ba2-8511-918a62309665",
      "cover": null,
      "icon": null,
      "created_time": "2022-02-15T21:09:00.000Z",
      "created_by": {
        "object": "user",
        "id": "71e95936-2737-4e11-b03d-f174f6f13087"
      },
      "last_edited_by": {
        "object": "user",
        "id": "5ba97cc9-e5e0-4363-b33a-1d80a635577f"
      },
      "last_edited_time": "2022-02-17T18:43:00.000Z",
      "title": [
        {
          "type": "text",
          "text": {
            "content": "Tasks",
            "link": null
          },
          "annotations": {
            "bold": false,
            "italic": false,
            "strikethrough": false,
            "underline": false,
            "code": false,
            "color": "default"
          },
          "plain_text": "Tasks",
          "href": null
        }
      ],
      "properties": {
        "Tags": {
          "id": "keGJ",
          "name": "Tags",
          "type": "multi_select",
          "multi_select": {
            "options": []
          }
        },
        "Name": {
          "id": "title",
          "name": "Name",
          "type": "title",
          "title": {}
        }
      },
      "parent": {
        "type": "page_id",
        "page_id": "e722caec-ae02-4a41-9bbd-286f65f8dca4"
      },
      "url": "https://notion.so/e8d49c2d96444ba28511918a62309665",
      "archived": false
    }
    ```
  </CodeGroup>

  We have also added a boolean `archived` property for [database objects](/reference/database) to denote if the database has been deleted. You can use the `archived` property to archive or unarchive a database and its descendants when [updating the database](/reference/update-a-database).
</Update>

<Update label="February 25, 2022">
  ### Releasing Notion-Version 2022-02-22

  <Note>
    **Notion's API versions**

    As a reminder, we only version backwards incompatible changes, so generally, you still get access to new features we release on the API without needing to upgrade. You can use different version headers for each request, so you can upgrade incrementally to get to the latest version.
  </Note>

  We're releasing Notion-Version `2022-02-22` with the following *backwards incompatible* changes:

  * `text` in blocks has been renamed to `rich_text`, to be consistent with the database property type.

  * Query database filter changes:

    * `phone` and `text` are no longer supported in query database filters when filtering by `phone_number` and `rich_text` properties. Use `phone_number` and `rich_text` instead.
    * `rollup` query database filters no longer accept the `text` keyword. Use `rich_text` instead.
    * `formula` query database filters no longer accept the `text` keyword. Use `string` instead.

  * `property_item` objects now return a `type`, `next_url`, and `id`.

  * Deprecated the List Databases API endpoint.

  #### The `text` property in content blocks has been renamed to `rich_text`

  To be consistent with the database property type, we have renamed the `text` property to `rich_text`. This affects the following block types: `paragraph`, `heading_1`, `heading_2`, `heading_3`, `callout`, `quote`, `bulleted_list_item`, `numbered_list_item`, `to_do` ,`toggle`, `code` ,`template`.

  Here is an example of the previous `text` property:

  <CodeGroup>
    ```json Previous paragraph block theme={null}
    {
      "type": "paragraph",
      //...other keys excluded
      "paragraph": {
        "text": [{
          "type": "text",
          "text": {
            "content": "Lacinato kale",
            "link": null
          }
        }]
      }
    }
    ```
  </CodeGroup>

  Here is an example of the updated `rich_text` property:

  <CodeGroup>
    ```json Updated paragraph block theme={null}
    {
      "type": "paragraph",
      //...other keys excluded
      "paragraph": {
        "rich_text": [{
          "type": "text",
          "text": {
            "content": "Lacinato kale",
            "link": null
          }
        }]
      }
    }
    ```
  </CodeGroup>

  #### Query database filter changes

  *`phone` and `text` no longer supported*

  Version 2022-02-22 no longer supports `phone` and `text` property filters in the query database endpoint. For consistency with the database property types, use `phone_number` and `rich_text` instead when filtering on `phone_number` and `rich_text` properties.

  More concretely, this query database filter will throw a validation error:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"filter": {
    		"and": [
    			{
    				"property": "Phone number",
    				"phone": {
    					"equals": "1112223333"
    				}
    			}
    		]
    	}
    }
    ```
  </CodeGroup>

  This query database filter will succeed:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"filter": {
    		"and": [
    			{
    				"property": "Phone number",
    				"phone_number": {
    					"equals": "1112223333"
    				}
    			}
    		]
    	}
    }
    ```
  </CodeGroup>

  *`rollup` property filters accept `rich_text` instead of `text`*

  Rollup property filters must now be constructed with the `rich_text` keyword instead of the `text` keyword if the value of the rollup is an array of `rich_text`. Put concretely, if a page's rollup property is rendered like so:

  <CodeGroup>
    ```json JSON expandable theme={null}
    "rollup property": {
    	"id": "~%5Bw%5C",
    	"type": "rollup",
    	"rollup": {
    		"type": "array",
    		"array": [
    			{
    				"type": "rich_text",
    				"rich_text": [
    					{
    						"type": "text",
    						"text": {
    							"content": "update text 2",
    							"link": null
    						},
    						"annotations": {
    							"bold": true,
    							"italic": false,
    							"strikethrough": false,
    							"underline": false,
    							"code": false,
    							"color": "red"
    						},
    						"plain_text": "update text 2",
    						"href": null
    					}
    				]
    			},
    			{
    				"type": "rich_text",
    				"rich_text": [
    					{
    						"type": "text",
    						"text": {
    							"content": "another text",
    							"link": null
    						},
    						"annotations": {
    							"bold": false,
    							"italic": false,
    							"strikethrough": false,
    							"underline": false,
    							"code": false,
    							"color": "default"
    						},
    						"plain_text": "another text",
    						"href": null
    					}
    				]
    			}
    		],
    		"function": "show_original"
    	}
    }
    ```
  </CodeGroup>

  This filter will no longer work in version 2022-02-22:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"filter": {
    		"property": "rollup property",
    		"rollup": {
    			"any": {
    				"text": {
    					"contains": "update text"
    				}
    			}
    		}
    	}
    }
    ```
  </CodeGroup>

  Instead, write:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"filter": {
    		"property": "rollup property",
    		"rollup": {
    			"any": {
    				"rich_text": {
    					"contains": "update text"
    				}
    			}
    		}
    	}
    }
    ```
  </CodeGroup>

  *`formula` property filters accept `string` instead of `text`*

  Rollup property filters must now be constructed with the `string` keyword instead of the `text` keyword if the value of the formula is a `string`. Put concretely, if a page's formula property is rendered like so:

  <CodeGroup>
    ```json JSON theme={null}
    "formula property": {
    	"id": "m%5D%3F%5C",
    	"type": "formula",
    	"formula": {
    		"type": "string",
    		"string": "update text 2,another text"
    	}
    }
    ```
  </CodeGroup>

  This filter will no longer work in version 2022-02-22:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"filter": {
    		"property": "formula property",
    		"formula": {
    			"text": {
    				"contains": "update text"
    			}
    		}
    	}
    }
    ```
  </CodeGroup>

  Instead, write this:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"filter": {
    		"property": "formula property",
    		"formula": {
    			"string": {
    				"contains": "update text"
    			}
    		}
    	}
    }
    ```
  </CodeGroup>

  ### Property list items now have types

  Property item lists now always have type `property_item`. Rollup aggregations are now returned inside that type.

  We've also added the property `id` field and the `next_url` to fetch the next set of property items.

  Here is an example of a previous `rollup` `property_item` list:

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "object": "list",
      "results": [
        {
          "object": "property_item",
          "type": "relation",
          "relation": {
            "id": "83f92c9d-523d-466e-8c1f-9bc2c25a99fe"
          }
        },
     		...
      ],
      "next_cursor": "some-next-cursor-value",
      "has_more": true,
      "rollup": {
        "type": "date",
        "date": {
          "start": "2021-10-07T14:42:00.000+00:00",
          "end": null
        },
        "function": "latest_date"
      },
      "type": "rollup"
    }
    ```
  </CodeGroup>

  Here is an example of the updated `rollup` `property_item` list:

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "object": "list",
      "results": [
        {
          "object": "property_item",
          "id": "xYz890",
          "type": "relation",
          "relation": {
            "id": "83f92c9d-523d-466e-8c1f-9bc2c25a99fe"
          }
        },
     		...
      ],
      "next_cursor": "some-next-cursor-value",
      "has_more": true,
      "type": "property_item",
      "property_item": {
        "id": "aBcD123"
        "next_url": "https://api.notion.com/v1/pages/b55c9c91-384d-452b-81db-d1ef79372b75/properties/aBcD123?start_cursor=some-next-cursor-value",
        "type": "rollup",
        "rollup": {
        	"type": "date",
        	"date": {
          	"start": "2021-10-07T14:42:00.000+00:00",
          	"end": null
        	},
        	"function": "latest_date"
    		}
      },

    }
    ```
  </CodeGroup>

  ### Deprecated the List Databases endpoint

  List all [Databases](/reference/database) endpoint is removed starting in this version. You can use the [Search API](/reference/post-search) for this functionality instead. The List Databases endpoint only returns explicitly shared databases, while search will also return child pages and databases within explicitly shared pages.
</Update>

<Update label="January 31, 2022 - February 13, 2022">
  <Note>
    **We're trying something new**

    We're experimenting with publishing biweekly changelogs in addition to our existing changelogs about new features. The biweekly changelogs will include bug fixes and improvements that are not big enough to justify their own changelog entry.

    The timing may be somewhat irregular until we smooth the process out, but we hope to align on a regular schedule soon. This is our first regular changelog entry; we hope you find it useful.
  </Note>

  ### Bug fixes and performance improvements

  * We added an optimization for search when filtering by pages or databases. This should particularly help latency when using search to power a database picker in a large workspace. For more details about search and how to optimize search requests, see the [search documentation](/reference/post-search).
  * We fixed an issue where fetching an embed block containing an uploaded file returned the wrong file URL.
</Update>

<Update label="January 25, 2022">
  ### Caption property is now supported for code block type

  We have added support for adding, updating, and retrieving the `caption` property for `code` block types.

  Below is an example response from [append block children](/reference/patch-block-children) containing a code block, with a caption, uploaded to Notion.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "block-id",
                "created_time": "2021-10-14T18:10:00.000Z",
                "last_edited_time": "2021-10-14T18:10:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "code",
                "code": {
                    "caption": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Hello Caption!",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "Hello Caption!",
                            "href": null
                        }
                    ],
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "const foo = \"bar\"",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "const foo = \"bar\"",
                            "href": null
                        }
                    ],
                    "language": "javascript"
                }
            },
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>
</Update>

<Update label="January 5, 2022">
  We have added support for simple tables in the API.

  ### Simple tables and simple table rows

  Tables are parent blocks for table row children. They can only contain children of type `table_row`.

  When creating a table block via the [Append block children](/reference/patch-block-children) endpoint, the `table` must have at least 1 `table_row` whose `cells` array has the same length as the `table_width`.

  To fetch content for a `table`, fetch the the `table_row` children via [Retrieve block children](/reference/get-block-children). The `table` block itself only contains formatting data, no content.

  Table block example:

  <CodeGroup>
    ```json JSON theme={null}
    {
    	"type": "table",
    	"table": {
    		"table_width": 3,
    		"has_column_header": false,
    		"has_row_header": false
    	}
    }
    ```
  </CodeGroup>

  Table row block example:

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "type": "table_row",
      "table_row": {
        "cells": [
          [
            {
              "type": "text",
              "text": {
                "content": "column 1 content",
                "link": null
              },
              "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
              },
              "plain_text": "column 1 content",
              "href": null
            }
          ],
          [
            {
              "type": "text",
              "text": {
                "content": "column 2 content",
                "link": null
              },
              "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
              },
              "plain_text": "column 2 content",
              "href": null
            }
          ],
          [
            {
              "type": "text",
              "text": {
                "content": "column 3 content",
                "link": null
              },
              "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
              },
              "plain_text": "column 3 content",
              "href": null
            }
          ]
        ]
      }
    }
    ```
  </CodeGroup>

  For more details, refer to the [Block object](/reference/block) docs.
</Update>

<Update label="December 15, 2021">
  Both public and internal integrations now support having more granular capabilities, which enforce what an integration can do and see in a Notion workspace. These capabilities when put together enforce which API endpoints an integration can call, and what content and user related information they are able to see. For further information on capabilities and best practices, see the [capabilities reference](/reference/capabilities).

  ### Content capabilities

  Integrations can have any combination of read content, insert content, or update content capabilities.

  * The **read content** capability gives the integration access to read existing content in a Notion workspace.
  * The **insert content** capability gives the integration permission to create new content in a Notion workspace.
  * The **update content** capability gives the integration permission to update existing content in a Notion workspace.

  ### User capabilities

  Integrations have different levels of user capabilities, which affect how [user objects](/reference/user) are returned from the Notion API:

  * No user information - the integration will not be able to request any information about users. User objects will not include information about the user, including name, profile images, or their email address.
  * User information without email addresses - user objects will include other information about the user, including their name or profile images, but omit the email address.
  * User information with email addresses - user objects will include all information about the user, including name, profile images, and their email address.

  ### Limitations

  An installed integration can never capabilities will never supersede the capabilities of the user who owns the integration. For example, an integration cannot insert or update on a page if the owner has read-only access.

  ### Existing integrations

  All existing integrations will continue to have the same functionality as before. Any integrations created before December 15, 2021 automatically will have all content capabilities, and user capabilities that give access to user information including email addresses.

  ### Updating integrations

  Update the capabilities on an existing integration through <a href={developerConnectionsUrl}>integrations dashboard</a>. After updating a public integration's capabilities, users will need to re-authenticate with the integration to apply the new capabilities to their installation. After re-authenticating a public integration with changed capabilities, or updating an internal integration with changed capabilities, the new capabilities will apply to all pages already shared with the integration. For more information on setting capabilities see the [Authorization](/guides/get-started/authorization) guide.
</Update>

<Update label="December 14, 2021">
  ### Time zone support

  We have added an optional `time_zone` field (based on the [IANA database](https://www.iana.org/time-zones) time zone values) to the Date objects. Developers can now explicitly set the time zones of Date property values using the `time_zone` field. Once this property is set explicitly, users will be able to see the same time zone in the app. When time zone information is provided in this method, `start` and `end` cannot contain [UTC offset](https://en.wikipedia.org/wiki/UTC_offset)s. In addition when time zone information is provided in dates, `start` and `end` cannot be dates without time information (i.e. `"2020-12-08"`).

  The public API will always return the `time_zone` field as `null` when rendering dates and time zone will be displayed as a [UTC offset](https://en.wikipedia.org/wiki/UTC_offset) in the `start` and `end` date fields.
</Update>

<Update label="November 17, 2021">
  ### Synced Block, Link to Page and Template block types are now supported in the API

  We have added support for adding and retrieving `synced_block`, `link_to_page` and `template` block types.

  #### `synced_block` block type

  Similar to the UI, there are two versions of a `synced_block` -- the original block that was created first and doesn't yet sync with anything else, and the reference blocks that are synced to the original synced block.

  **Original Synced Block** To create a `synced_block`, the developer needs to create an original synced block. Developers will be able to identify the original `synced_block` because it does not "sync\_from" any other block (i.e. the `synced_from` property is set to `null`).

  This is an example of an "original" `synced_block`. Note that all of the blocks available to be synced in another `synced_block` are captured in the `children` property.

  <CodeGroup>
    ```json synced_block (original) theme={null}
    {
        "type": "synced_block",
        "synced_block": {
            "synced_from": null,
            "children": [
                {
                    "callout": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Callout in synced block"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
    ```
  </CodeGroup>

  **Reference Synced Blocks** To sync the content of the original `synced_block` with another `synced_block`, the developer simply needs to refer to that `synced_block` using the `synced_from` property.

  Below is an example of a `synced_block` referring to another `synced_block`. Note that only "original" synced blocks can be referenced in the `synced_from` property.

  <CodeGroup>
    ```json synced_block (reference to original) in request body theme={null}
    {
        "type": "synced_block",
        "synced_block": {
            "synced_from": {
                "block_id": "original_synced_block_id"
            }
        }
    }
    ```
  </CodeGroup>

  Below is the example response after creating the `synced_block` above. We can tell that the content from the original synced block is synced with this one because this block has children even though we didn't explicitly set the children in the body of our API call above (i.e. `has_children` property on the reference block is `true`).

  <CodeGroup>
    ```json synced_block (reference to original) in response body theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "block_id",
                "created_time": "2021-11-17T22:17:00.000Z",
                "last_edited_time": "2021-11-17T22:17:00.000Z",
                "has_children": true,
                "archived": false,
                "type": "synced_block",
                "synced_block": {
                    "synced_from": {
                        "type": "block_id",
                        "block_id": "original_synced_block_id"
                    }
                }
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  <Warning>
    **Important notes**

    1. The bot must have access to both the original and reference synced blocks
    2. Similar to the UI, we don't support changes to `synced_from` at this time
  </Warning>

  #### `link_to_page` block type

  We have added support for adding and retrieving `link_to_page` block types. Using this block type, developers can now create page links to other pages (using the `page_id` property) and full page databases (using the `database_id` property).

  Below is an example request body for the [append block children](/reference/patch-block-children) endpoint containing a `link_to_page` block type.

  <CodeGroup>
    ```json link_to_page block type used in request body theme={null}
    {
        "children": [
            {
                "type": "link_to_page",
                "link_to_page": {
                    "type": "page_id",
                    "page_id": "61cca5bd-c8c6-4fcc-b517-514da3b8b1e0"
                }
            }
        ]
    }
    ```
  </CodeGroup>

  #### `template` block type

  We have added support for adding and retrieving `template` block types. Using this block type, developers can now create template that duplicates the its children blocks.

  Below is an example request body for the [append block children](/reference/patch-block-children) endpoint containing a `template` block type.

  <CodeGroup>
    ```json template_block type used in request body expandable theme={null}
    {
        "children": [
            {
                "type": "template",
                "template": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Create callout template"
                            }
                        }
                    ],
                    "children": [
                        {
                            "callout": {
                                "text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": "Placeholder callout text"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        ]
    }
    ```
  </CodeGroup>
</Update>

<Update label="November 10, 2021">
  The public API now supports returning `link_preview` blocks and mentions found in `rich_text`! Previously these blocks had type `unsupported` and mentions were skipped in `rich_text`. Note: `link_preview`s cannot be created via the API, only returned in responses.

  See the documentation in [blocks](/reference/block#link-preview) and [`rich_text`](/reference/rich-text#link-preview-mention-type-object) for more information.

  <CodeGroup>
    ```json JSON theme={null}
    {
      "type": "link_preview",
      //...other keys excluded
      "link_preview": {
        "url": "https://github.com/example/example-repo/pull/1234"
      }
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 25, 2021">
  We have added support for `column_list` and `column` block types.

  You can now add Column Lists and Columns to pages and other block types.

  Column Lists are parent blocks for column children. They can only contain children of type `column`.

  Columns are parent blocks for any supported block children, excluding `column`s. They can only be appended to `column_list`s.

  When initially creating a column list block via [Append block children](/reference/patch-block-children), the column list must have at least 2 columns, and those columns must have at least one child each.

  When fetching content for a column\_list, first fetch the the column children via [Retrieve block children](/reference/get-block-children). Then fetch the children for each column block.

  Below is an example request body for appending `column_list` and nested `column` children.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "children": [
        {
          "object": "block",
          "type": "column_list",
          "column_list": {
            "children": [
              {
                "object": "block",
                "type": "column",
                "column": {
                  "children": [
                    {
                      "object": "block",
                      "type": "paragraph",
                      "paragraph": {
                        "text": [
                          {
                            "type": "text",
                            "text": {
                              "content": "some text here"
                            }
                          }
                        ]
                      }
                    }
                  ]
                }
              },
              {
                "object": "block",
                "type": "column",
                "column": {
                  "children": [
                    {
                      "object": "block",
                      "type": "paragraph",
                      "paragraph": {
                        "text": [
                          {
                            "type": "text",
                            "text": {
                              "content": "some text here"
                            }
                          }
                        ]
                      }
                    }
                  ]
                }
              }
            ]
          }
        }
      ]
    }
    ```
  </CodeGroup>

  Below is an example response of appending `column_list` children.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "ca042aa7-2e23-4541-8059-abff360d6752",
                "created_time": "2021-10-25T17:00:00.000Z",
                "last_edited_time": "2021-10-25T17:00:00.000Z",
                "has_children": true,
                "archived": false,
                "type": "column_list",
                "column_list": {}
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  Below is an example request body for appending `column` children. Note that the parent that is being added to must be a block of type `column_list`.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "children": [
            {
                "object": "block",
                "type": "column",
                "column": {
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": "some text here"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        ]
    }
    ```
  </CodeGroup>

  Below is an example response of appending `column` children.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "f40c3a13-30d1-4594-bd6f-cdbc15b2c006",
                "created_time": "2021-10-25T21:25:00.000Z",
                "last_edited_time": "2021-10-25T21:25:00.000Z",
                "has_children": true,
                "archived": false,
                "type": "column",
                "column": {}
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 18, 2021">
  ### Validation on embed block URLs

  The public API will now return errors on embeds blocks that are not supported by the public API. The supported embed block types (as listed and kept up to date in the [Block Object](/reference/block#embed) documentation):

  * Framer
  * Twitter (tweets)
  * Google Drive documents
  * Gist
  * Figma
  * Invision,
  * Loom
  * Typeform
  * Codepen
  * PDFs
  * Google Maps
  * Whimisical
  * Miro
  * Abstract
  * Excalidraw
  * Sketch
  * Replit

  Previously failed embeds would return a successful request, but produce an error in the Notion Application. Failed embed requests will now return a 400 Client Error.

  For non embed URLs, consider using the `bookmark` or `image` block types.
</Update>

<Update label="October 17, 2021">
  ### Dates with times and timezones are now supported on Database Date Filters

  Previously, the date filters `equals`, `after`, `before`, `on_or_after`, and `on_or_before` only supported dates without times nor timezones.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "filter": {
            "or": [
                {
                    "property": "My Time Property",
                    "date": {
                        "before": "2021-10-20"
                    }
                }
            ]
        },
        "sorts": []
    }
    ```
  </CodeGroup>

  Now the database date filters can accept ISO 8601 dates with timestamps and timezones.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "filter": {
            "or": [
                {
                    "property": "My Time Property",
                    "date": {
                        "before": "2021-10-15T12:00:00-07:00"
                    }
                }
            ]
        },
        "sorts": []
    }
    ```
  </CodeGroup>

  <Note>
    **How Dates with times are compared**

    Date time comparisons are done with millisecond precision. If no timezone is provided, the default is UTC.
  </Note>

  <Note>
    **Equals Date filter**

    If a date without a time is provided to the `equals`, the comparison is done against the start and end of the UTC date provided (inclusive). If a date with a time is provided, the comparison is done with millisecond precision. If no timezone is provided, the default timezone is UTC.
  </Note>
</Update>

<Update label="October 15, 2021">
  ### Breadcrumb block types are now supported in the API

  We have added support for adding and retrieving `Breadcrumb` block types.

  You can now can add Breadcrumb blocks to pages and other blocks.

  Below is an example response from [Append block children](/reference/patch-block-children) containing a Breadcrumb block uploaded to Notion.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "block-id",
                "created_time": "2021-10-14T18:10:00.000Z",
                "last_edited_time": "2021-10-14T18:10:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "breadcrumb",
                "breadcrumb": {}
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 14, 2021">
  ### Table of contents and divider block types are now supported

  We have added support for adding and retrieving `Table of Contents` and `Divider` block types.

  ### Table of Contents blocks

  You can now can add Table of Contents blocks to pages and other blocks.

  Below is an example response from [Append block children](/reference/patch-block-children) containing a Table of Contents block uploaded to Notion.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "block-id",
                "created_time": "2021-10-14T18:10:00.000Z",
                "last_edited_time": "2021-10-14T18:10:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "table_of_contents",
                "table_of_contents": {}
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  ### Divider blocks

  You can now can add Divider blocks to pages and other blocks.

  Below is an example response from [Append block children](/reference/patch-block-children) containing a Divider block uploaded to Notion.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "block-id",
                "created_time": "2021-10-14T18:10:00.000Z",
                "last_edited_time": "2021-10-14T18:10:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "divider",
                "divider": {}
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 11, 2021">
  ### Users can now add Equation Blocks, Embed, Bookmark, and Media Blocks

  We have added support for retrieving, adding and updating Equation Blocks. We have also added support for updating Embed, Bookmark and Media (including image, video, audio, file, pdf) block types.

  #### Equation Blocks

  You can now can add, retrieve, and update equation blocks when using the [Append block children](/reference/patch-block-children) , [Retrieve block children](/reference/get-block-children) and [Update block](/reference/update-a-block) API endpoints.

  Below is an example response from [Append block children](/reference/patch-block-children) containing an equation block uploaded to Notion.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "2d97bf53-7e79-4efd-a6b2-53c0026ed1b5",
                "created_time": "2021-10-11T17:56:00.000Z",
                "last_edited_time": "2021-10-11T17:56:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "equation",
                "equation": {
                    "expression": "e = mc^2"
                }
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  #### Media Blocks (video, audio, image, file, pdf)

  You can now can update media blocks when using [Update block](/reference/update-a-block).

  <Note>
    **Only media blocks of type external are supported**

    Updated Media blocks must be of type "external" and must reference an external URL. File upload is not currently supported.
  </Note>

  Below is an example response from [Update block](/reference/update-a-block) containing a video block uploaded to Notion.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "block",
        "id": "37af9d6e-290a-488b-9d53-fb4b983f8289",
        "created_time": "2021-10-12T23:11:00.000Z",
        "last_edited_time": "2021-10-12T23:12:00.000Z",
        "has_children": false,
        "archived": false,
        "type": "video",
        "video": {
            "caption": [
                {
                    "type": "text",
                    "text": {
                        "content": "My caption",
                        "link": null
                    },
                    "annotations": {
                        "bold": false,
                        "italic": false,
                        "strikethrough": false,
                        "underline": false,
                        "code": false,
                        "color": "default"
                    },
                    "plain_text": "My caption",
                    "href": null
                }
            ],
            "type": "external",
            "external": {
                "url": "https://www.youtube.com/watch?v=aA7si7AmPkY"
            }
        }
    }
    ```
  </CodeGroup>

  #### Embed and Bookmark Block Types

  You can now can update embed and bookmark blocks when using [Update block](/reference/update-a-block).

  Below is an example response from [Update block](/reference/update-a-block) containing a bookmark block uploaded to Notion.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "block",
        "id": "050010f8-d164-4f5d-85a0-fc9db4598107",
        "created_time": "2021-10-12T23:05:00.000Z",
        "last_edited_time": "2021-10-12T23:06:00.000Z",
        "has_children": false,
        "archived": false,
        "type": "bookmark",
        "bookmark": {
            "caption": [
                {
                    "type": "text",
                    "text": {
                        "content": "My caption",
                        "link": null
                    },
                    "annotations": {
                        "bold": false,
                        "italic": false,
                        "strikethrough": false,
                        "underline": false,
                        "code": false,
                        "color": "default"
                    },
                    "plain_text": "My caption",
                    "href": null
                }
            ],
            "url": "http://www.notion.so"
        }
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 7, 2021">
  ### Users can now add and update Callout and Quote block types

  <Warning>
    **New API endpoints and block types not supported in older versions of the API as of September 28**

    As of September 28, 2021, new block types and API endpoints will *not* be supported in older versions of the API. If you're currently on version `2021-05-11` or `2021-05-13`, upgrade to `2021-08-16` to take advantage of the new block types in this changelog and any other block types or endpoints introduced after September 28.

    API functionality introduced before September 28 will continue to work with older API versions.
  </Warning>

  We have added support for retrieving, adding and updating quote and callout block types.

  #### Quote blocks

  You can now can add and retrieve quote blocks when using [Append block children](/reference/patch-block-children) and [Retrieve block children](/reference/get-block-children).

  Below is an example response from [Append block children](/reference/patch-block-children) containing a quote block uploaded to Notion.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "block-id",
                "created_time": "2021-10-07T19:21:00.000Z",
                "last_edited_time": "2021-10-07T19:21:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "quote",
                "quote": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "The digital revolution is far more significant than the invention of writing or even of printing.",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": true,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "The digital revolution is far more significant than the invention of writing or even of printing.",
                            "href": null
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "\n-Douglas Engelbart",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "\n-Douglas Engelbart",
                            "href": null
                        }
                    ]
                }
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  #### Callout blocks

  You can now can add and retrieve callout blocks when using [Append block children](/reference/patch-block-children) and [Retrieve block children](/reference/get-block-children).

  Below is an example response from [Retrieve block](/reference/retrieve-a-block) containing a callout block uploaded to Notion.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "block",
        "id": "block-id",
        "created_time": "2021-10-07T19:23:00.000Z",
        "last_edited_time": "2021-10-07T19:24:00.000Z",
        "has_children": false,
        "archived": false,
        "type": "callout",
        "callout": {
            "text": [
                {
                    "type": "text",
                    "text": {
                        "content": "Note: Something special is happening above",
                        "link": null
                    },
                    "annotations": {
                        "bold": false,
                        "italic": false,
                        "strikethrough": false,
                        "underline": false,
                        "code": false,
                        "color": "default"
                    },
                    "plain_text": "Note: Something special is happening above",
                    "href": null
                }
            ],
            "icon": {
                "type": "emoji",
                "emoji": "💡"
            }
        }
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 5, 2021">
  ### Retrieve page property item

  Developers can now individually retrieve the value of their page properties with the [Retrieve a page property](/reference/retrieve-a-page-property) endpoint! This includes pagination through a list of property item objects for properties with long values or lots of page references such as formula, relations and rollups. See the [documentation](/reference/retrieve-a-page-property) for more info.

  Use the [Retrieve a database](/reference/retrieve-a-database) endpoint to obtain the `property_id` .

  **Simple Property Types**

  Most properties will be identified by a `type` with the property value in the object found in key `{type}`.

  *Example Request/Response*

  <CodeGroup>
    ```bash cURL theme={null}
    curl --request GET \
      --url http://localhost:3000/v1/pages/b55c9c91-384d-452b-81db-d1ef79372b75/properties/some-property-id \
      --header 'Authorization: Bearer $NOTION_API_KEY' \
      --header 'Notion-Version: 2021-08-16'
    ```
  </CodeGroup>

  <CodeGroup>
    ```json JSON theme={null}
    {
      "object": "property_item",
      "type": "number",
      "number": 2
    }
    ```
  </CodeGroup>

  **Paginated Property Types**

  Properties of type `title`, `rich_text`, `relation` and `people` will return a paginated list of [Property Item Objects](/reference/retrieve-a-page-property#property-item-objects)

  *Example List Response*

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "property_item",
                "type": "rich_text",
                "rich_text": {
                    "type": "text",
                    "text": {
                        "content": "Avocado ",
                        "link": null
                    },
                    "annotations": {
                        "bold": false,
                        "italic": false,
                        "strikethrough": false,
                        "underline": false,
                        "code": false,
                        "color": "default"
                    },
                    "plain_text": "Avocado ",
                    "href": null
                }
            },
    ... // additional results omitted.
        ],
        "next_cursor": "some-next-cursor-value",
        "has_more": true
    }
    ```
  </CodeGroup>

  **Rollup Property Types**

  Rollups of type 'Show Original', 'Show unique', 'Count unique' and 'Median' return a flattened list of property items. All other rollups are return a list of relations and (after pagination) a [rollup property value]() of type `date` or `number`.

  *Example Paginated Property Item Request/Response*

  A rollup page property with an aggregation that requires additional pagination.

  <CodeGroup>
    ```bash cURL theme={null}
    curl --request GET \
      --url http://localhost:3000/v1/pages/b55c9c91-384d-452b-81db-d1ef79372b75/properties/some-property-id?page_size=10&start_cursor=some-cursor-value \
      --header 'Authorization: Bearer $NOTION_API_KEY' \
      --header 'Notion-Version: 2021-08-16'
    ```
  </CodeGroup>

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "property_item",
                "type": "relation",
                "relation": {
                    "id": "de5d73e8-3748-40fa-9102-f1290fe2444b"
                }
            },
            {
                "object": "property_item",
                "type": "relation",
                "relation": {
                    "id": "164325b0-4c9e-416b-ba9c-037b4c9acdfd"
                }
            },
            {
                "object": "property_item",
                "type": "relation",
                "relation": {
                    "id": "456baa98-3239-4c1f-b0ea-bdae945aaf33"
                }
            }
          ...
        ],
        "next_cursor": "some-next-cursor-value",
        "has_more": true,
        "rollup": {
            "type": "date",
            "date": {
                "start": "2021-10-07T14:42:00.000+00:00",
                "end": null
            },
            "function": "latest_date"
        },
        "type": "rollup"
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 4, 2021">
  ### Retrieve your token's bot user with GET /v1/users/me

  If you're using Notion API version `2021-08-16`, you can now retrieve information about the bot associated with your API token, including its ID and the user who authorized it.

  **Example request**

  <CodeGroup>
    ```bash cURL theme={null}
    curl --request GET \
      --url http://localhost:3000/v1/users/me \
      --header 'Authorization: Bearer $NOTION_API_KEY' \
      --header 'Notion-Version: 2021-08-16'
    ```
  </CodeGroup>

  **Example response**

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "object": "user",
      "id": "16d84278-ab0e-484c-9bdd-b35da3bd8905",
      "name": "pied piper",
      "avatar_url": null,
      "type": "bot",
      "bot": {
        "owner": {
          "type": "user",
          "user": {
            "object": "user",
            "id": "5389a034-eb5c-47b5-8a9e-f79c99ef166c",
            "name": "christine makenotion",
            "avatar_url": null,
            "type": "person",
            "person": {
              "email": "christine@makenotion.com"
            }
          }
        }
      }
    }
    ```
  </CodeGroup>
</Update>

<Update label="October 1, 2021">
  ### New functionality not available to old API versions; code, inline databases, and database page block

  <Warning>
    **New API endpoints and block types not supported in older versions of the API as of September 28**

    As of September 28, 2021, new block types and API endpoints will *not* be supported in older versions of the API. If you're currently on version `2021-05-11` or `2021-05-13`, upgrade to `2021-08-16` to take advantage of the new block types in this changelog and any other block types or endpoints introduced after September 28.

    API functionality introduced before September 28 will continue to work with older API versions.
  </Warning>

  We have added support for retrieving, adding and updating code blocks, inline databases and database page blocks.

  **Code blocks**

  You can now can retrieve and add code blocks when using [Append block children](/reference/patch-block-children) and [Retrieve block children](/reference/get-block-children).

  Below is an example response from [Retrieve block children](/reference/get-block-children) containing a code block uploaded to Notion.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "ee27cd42-eaad-467f-9956-c0aa4efa94b5",
                "created_time": "2021-09-22T20:27:00.000Z",
                "last_edited_time": "2021-09-27T19:25:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "code",
                "code": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "const a = 21\nconst b = a + 5",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "const a = 21\nconst b = a + 5",
                            "href": null
                        }
                    ],
                    "language": "javascript"
                }
            },
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  **Inline databases and database page blocks**

  You can now can retrieve child database blocks when using [Retrieve block children](/reference/get-block-children) and [Retrieve block](/reference/retrieve-a-block).

  <Note>
    **Updating `child_database` blocks**

    To update `child_database` type blocks, use the [Update database](/reference/update-a-database) endpoint. Updating the block's `title` updates the text displayed in the associated `child_database` block.
  </Note>

  Below is an example response from [Retrieve block children](/reference/get-block-children) containing a child database uploaded to Notion.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "0d6ff4f9-1211-4129-ab4a-19dfc33d4d7a",
                "created_time": "2021-09-27T20:25:00.000Z",
                "last_edited_time": "2021-09-27T20:25:00.000Z",
                "has_children": false,
                "archived": false,
                "type": "child_database",
                "child_database": {
                    "title": "My child database"
                }
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>
</Update>

<Update label="September 21, 2021">
  ### Workspace-level tokens for public integrations will be deprecated soon; migrate your OAuth flows

  Starting today we will be changing who can authorize public integrations in Notion workspaces. The previously released authorization method will be fully deprecated on October 19.

  #### About the change

  Currently OAuth tokens function on a workspace level: only admins in a workspace can grant access and there can only be one token per workspace per integration. After a brief transition period (see "How to prepare for this change" below) we will be switching exclusively to user-level tokens. These can be granted by any admin or member in the workspace, and there can be as many tokens per workspace as there are admins and members in the workspace.

  See the table for the differences between these two methods:

  |                                                                   | Workspace-level tokens (old)                                                                                                                                                                                                                                       | User-level tokens (new)                                                                                                                                                                                                            |
  | :---------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | Who can go through OAuth and grant access                         | Admins only                                                                                                                                                                                                                                                        | Admins and members                                                                                                                                                                                                                 |
  | Number of access tokens per workspace                             | 1                                                                                                                                                                                                                                                                  | Up to N, where N is the number of admins and members                                                                                                                                                                               |
  | Who can go through OAuth and reauthorize access for a given token | Only the original user who went through OAuth to grant the token                                                                                                                                                                                                   | Only the original user who went through OAuth to grant the token                                                                                                                                                                   |
  | OAuth token response                                              | Contains an `owner` field with the value `{ workspace: true }`                                                                                                                                                                                                     | Contains an `owner` field with the value `{ user: <API user object> }`                                                                                                                                                             |
  | What resources an integration has access to                       | Pages/databases the installing user chooses via the page picker during OAuth; pages/databases the installing user and other users in the workspace share with the integration via the Page menu; children of pages/databases that were shared with the integration | Pages/databases the installing user chooses via the page picker during OAuth; pages/databases the installing user shares with the integration via the Page menu; children of pages/databases that were shared with the integration |
  | What an integration can do with resources it has access to        | Read and write                                                                                                                                                                                                                                                     | Read and write                                                                                                                                                                                                                     |

  #### How to prepare for this change:

  This change only affects public integrations; that is, integrations that can be installed across many workspaces via OAuth. It does not affect internal integrations.

  1. Ensure that you can store and handle multiple Notion API tokens per workspace where your integration is granted access. You may map tokens directly to the `bot_id` which is returned in the OAuth token response and is guaranteed to be unique per API token.
     * To avoid overwriting tokens, do not map the token to the `workspace_id` returned in the OAuth token response, since a workspace may have multiple tokens. Do not map the token to the `owner.user.id` in the OAuth token response, since a user may install your integration in multiple workspaces.
  2. Add `&owner=user` to your OAuth authorization URL (the url starting with `https://api.notion.com/v1/oauth/authorize`) once your application is ready for user-level tokens.

  #### What to expect on October 19

  On October 19, we will migrate all existing workspace-level tokens to user-level tokens. We will also default to creating user-level tokens when a user goes through OAuth, regardless of the `owner` parameter in the OAuth URL.
</Update>

<Update label="September 17, 2021">
  ### Database objects now contain url

  [Database objects](/reference/database) now return the web address of the database in the `url` key.

  <CodeGroup>
    ```json cURL theme={null}
    {
    "object": "database",
    "id": "668d797c-76fa-4934-9b05-ad288df2d136",
    "created_time": "2020-03-17T19:10:04.968Z",
    "last_edited_time": "2020-03-17T21:49:37.913Z",
    "parent": {
      "type": "page_id",
      "page_id": "48f8fee9-cd79-4180-bc2f-ec0398253067"
    },
    "icon": {
      "type": "emoji",
        "emoji": "🎉"
    },
    "cover": {
      "type": "external",
      "external": {
        	"url": "https://website.domain/images/image.png"
      }
    },
    "url": "https://www.notion.so/668d797c76fa49349b05ad288df2d136",
    "title": [
      {
        "type": "text",
        "text": {
          "content": "Grocery List",
          "link": null
        },
        "annotations": {
          "bold": false,
          "italic": false,
          "strikethrough": false,
          "underline": false,
          "code": false,
          "color": "default"
        },
        "plain_text": "Grocery List",
        "href": null
      }
    ],
    "properties": {
      "Name": {
        "id": "title",
        "type": "title",
        "title": {}
      },
      "Description": {
        "id": "J@cS",
        "type": "rich_text",
        "rich_text": {}
      },
      "In stock": {
        "id": "{xY`",
        "type": "checkbox",
        "checkbox": {}
      },
      "Food group": {
        "id": "TJmr",
        "type": "select",
        "select": {
          "options": [
            {
              "id": "96eb622f-4b88-4283-919d-ece2fbed3841",
              "name": "🥦Vegetable",
              "color": "green"
            },
            {
              "id": "bb443819-81dc-46fb-882d-ebee6e22c432",
              "name": "🍎Fruit",
              "color": "red"
            },
            {
              "id": "7da9d1b9-8685-472e-9da3-3af57bdb221e",
              "name": "💪Protein",
              "color": "yellow"
            }
          ]
        }
      },
      "Price": {
        "id": "cU^N",
        "type": "number",
        "number": {
          "format": "dollar"
        }
      },
      "Cost of next trip": {
        "id": "p:sC",
        "type": "formula",
        "formula": {
          "value": "if(prop(\"In stock\"), 0, prop(\"Price\"))"
        }
      },
      "Last ordered": {
        "id": "]\\R[",
        "type": "date",
        "date": {}
      },
      "Meals": {
        "type": "relation",
        "relation": {
          "database": "668d797c-76fa-4934-9b05-ad288df2d136",
          "synced_property_name": null
        }
      },
      "Number of meals": {
        "id": "Z\\Eh",
        "type": "rollup",
        "rollup": {
          "rollup_property_name": "Name",
          "relation_property_name": "Meals",
          "rollup_property_id": "title",
          "relation_property_id": "mxp^",
          "function": "count"
        }
      },
      "Store availability": {
        "type": "multi_select",
        "multi_select": {
          "options": [
            [
              {
                "id": "d209b920-212c-4040-9d4a-bdf349dd8b2a",
                "name": "Duc Loi Market",
                "color": "blue"
              },
              {
                "id": "70104074-0f91-467b-9787-00d59e6e1e41",
                "name": "Rainbow Grocery",
                "color": "gray"
              },
              {
                "id": "e6fd4f04-894d-4fa7-8d8b-e92d08ebb604",
                "name": "Nijiya Market",
                "color": "purple"
              },
              {
                "id": "6c3867c5-d542-4f84-b6e9-a420c43094e7",
                "name": "Gus's Community Market",
                "color": "yellow"
              }
            ]
          ]
        }
      },
      "+1": {
        "id": "aGut",
        "type": "people",
        "people": {}
      },
      "Photo": {
        "id": "aTIT",
        "type": "files",
        "files": {}
      }
    }
    }
    ```
  </CodeGroup>
</Update>

<Update label="September 10, 2021">
  ### Users can now delete Block objects

  The Notion API now supports the [Delete a block](/reference/delete-a-block) endpoint for all supported block types (include pages). The endpoint mirrors the behavior in the Notion application UI where items are added to the "Trash" bucket. In addition, the [Block object](/reference/block) now returns a boolean `archived` field to denote if the block has been deleted.

  After deleting (archiving) the block, it can be unarchived using the [Update a block](/reference/update-a-block) or [Update page](/reference/patch-page) endpoint with the body `{ archived: false }`.

  #### Example Request

  <CodeGroup>
    ```bash cURL theme={null}
    curl 'https://api.notion.com/v1/blocks/9bc30ad4-9373-46a5-84ab-0a7845ee52e6' \
      -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
      -H 'Notion-Version: 2021-08-16'
      -X DELETE \
    ```
  </CodeGroup>

  #### Example response

  <CodeGroup>
    ```json JSON theme={null}
    {
      "object": "block",
      "id": "9bc30ad4-9373-46a5-84ab-0a7845ee52e6",
      "created_time": "2021-03-16T16:31:00.000Z",
      "last_edited_time": "2021-03-16T16:32:00.000Z",
      "has_children": false,
      "type": "to_do",
      "archived": true
      "to_do": {
        "text": [
          {
            "type": "text",
            "text": {
              "content": "Lacinato kale",
              "link": null
            },
            "annotations": {
              "bold": false,
              "italic": false,
              "strikethrough": false,
              "underline": false,
              "code": false,
              "color": "default"
            },
            "plain_text": "Lacinato kale",
            "href": null
          }
        ],
        "checked": false
      }
    }
    ```
  </CodeGroup>

  ## September 9, 2021

  ### Relation and rollup properties can now be created in databases

  When [creating](/reference/create-a-database) or [updating](/reference/update-a-database) databases, you can now add `relation` and `rollup` property types. Note that the related database must also be shared with the integration.

  #### Example request

  <CodeGroup>
    ```bash cURL theme={null}
    curl --location --request POST 'https://api.notion.com/v1/databases/' \
    --header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
    --header 'Content-Type: application/json' \
    --header 'Notion-Version: 2021-08-16' \
    --data '{
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                }
            }
        ],
        "properties": {
            "Name": {
                "title": {}
            },
            "Description": {
                "rich_text": {}
            },
            "In stock": {
                "checkbox": {}
            },
            "Meals": {
              "relation": {
                "database_id": "668d797c-76fa-4934-9b05-ad288df2d136",
              }
        		},
            "Number of meals": {
              "rollup": {
                "rollup_property_name": "Name",
                "relation_property_name": "Meals",
                "function": "count"
              }
            }
        }
    }'
    ```
  </CodeGroup>

  #### Example response

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "database",
        "id": "bc1211ca-e3f1-4939-ae34-5260b16f627c",
        "created_time": "2021-07-08T23:50:00.000Z",
        "last_edited_time": "2021-07-08T23:50:00.000Z",
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                },
                "annotations": {
                    "bold": false,
                    "italic": false,
                    "strikethrough": false,
                    "underline": false,
                    "code": false,
                    "color": "default"
                },
                "plain_text": "Grocery List",
                "href": null
            }
        ],
        "properties": {
           "Name": {
                "id": "title",
                "type": "title",
                "title": {}
            },
            "Description": {
                "id": "V}lX",
                "type": "rich_text",
                "rich_text": {}
            },
            "In stock": {
                "id": "V>GQ",
                "type": "checkbox",
                "checkbox": {}
            },
            "Meals": {
              "type": "relation",
              "relation": {
                "database_id": "668d797c-76fa-4934-9b05-ad288df2d136",
                "synced_property_name": "Related to Grocery List (Meals)"
              }
            },
            "Number of meals": {
              "id": "Z\\Eh",
              "type": "rollup",
              "rollup": {
                "rollup_property_name": "Name",
                "relation_property_name": "Meals",
                "rollup_property_id": "title",
                "relation_property_id": "mxp^",
                "function": "count"
              }
            },

        },
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        }
    }
    ```
  </CodeGroup>

  ## August 24, 2021

  ### Page icons, cover images, new block types, and improved page file properties

  We have added support for linking to external image and file URLs, and many new block types, including image, embed, and file blocks.

  You can now use the Notion API to:

  * Retrieve and update [page](/reference/page) and [database](/reference/database) icons and cover images.
  * [List](/reference/get-block-children) and [append](/reference/patch-block-children) embed, image, video, file, PDF, and bookmark blocks
  * Retrieve URL for [file page properties](/reference/page-property-values#files)
  * Update [file page properties](/reference/page-property-values#files)

  We do not yet support uploading files to Notion through the API, however, any files already uploaded to Notion can be retrieved. You can reference the details of what is supported [here](/reference/file-object).

  #### Page Icons and Cover Images

  When fetching a [Page object](/reference/page) or a [Database object](/reference/database), the response will now include an `icon` and `cover` property, as shown below:

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "database",
        "id": "96433ad8-3fbe-460f-a007-72311c4aa804",
        "cover": {
            "type": "external",
            "external": {
                "url": "https://website.domain/images/image.png"
            }
        },
        "icon": {
            "type": "emoji",
            "emoji": "🎉"
        },
        // ... remaining properties
    }
    ```
  </CodeGroup>

  The [Create a page](/reference/post-page), [Update page](/reference/patch-page), [Create a database](/reference/create-a-database), and [Update database](/reference/update-a-database) API endpoints now support the ability to set the page icon and cover image.

  #### New Block Types

  You can now can retrieve and add embed, image, video, file, pdf, and bookmark blocks when using [Append block children](/reference/patch-block-children) and [Retrieve block children](/reference/get-block-children).

  Below is an example response from [Retrieve a page](/reference/retrieve-a-page) containing an image uploaded to Notion.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "4896a9bf-ada2-4bec-8ea2-97bccf07c4ef",
                "created_time": "2021-08-20T21:12:00.000Z",
                "last_edited_time": "2021-08-20T21:12:00.000Z",
                "has_children": false,
                "type": "image",
                "image": {
                    "caption": [],
                    "type": "file",
                    "file": {
                        "url": "https://s3.us-west-2.amazonaws.com/secure.notion-static.com/64f658a7-eb31-4f98-8bea-0aa2956ec475/brocolli.jpeg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20210820%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20210820T211229Z&X-Amz-Expires=3600&X-Amz-Signature=e2adc496254ccc741d7ab4f3bab0de7a51b60e31a49d11fcf8702ead2ec9ec18&X-Amz-SignedHeaders=host",
                        "expiry_time": "2021-08-20T22:12:29.066Z"
                    }
                }
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  <Info>
    Third-party web applications, e.g. Typeform, Figma, etc., are retrieved and added as embed blocks.
  </Info>

  #### File Page Properties

  When retrieving file page properties, you'll now get a link to the file as well as the name.

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "page",
        "properties": {
            "Files": {
                "id": "YP~`",
                "type": "files",
                "files": [
                    {
                        "name": "Brocolli",
                        "type": "file",
                        "file": {
                            "url": "https://s3.us-west-2.amazonaws.com/secure.notion-static.com/c32db351-d1ea-40c2-9660-820db28c44ad/brocolli.jpeg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20210820%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20210820T211042Z&X-Amz-Expires=3600&X-Amz-Signature=859a24c9b7153860b252fa5955829a97632650dcdc5e91c7a831a48c5efecae4&X-Amz-SignedHeaders=host",
                            "expiry_time": "2021-08-20T22:10:42.022Z"
                        }
                    },
                    {
                        "name": "Text File",
                        "type": "external",
                        "external": {
                            "url": "https://website.domain/files/doc.txt"
                        }
                    }
                ]
            },
        },
        // ... remaining properties
    }
    ```
  </CodeGroup>

  We also support updating file page properties via [Update page](/reference/patch-page).

  ## August 20, 2021

  ### Releasing Notion-Version 2021-08-16

  We're releasing Notion-Version `2021-08-16` with the following *backwards incompatible* changes:

  * [Unknown Keys Will Fail Validation](#unknown-keys-will-fail-validation)
  * [Rollup Property Types](#changes-to-array-rollup-property-types)
  * [Append Block Children](#append-block-children-returns-a-list-of-blocks)
  * [URL Safe Property IDs](#property-ids-are-now-url-safe)
  * [Empty Properties Are Now Returned](#empty-database-properties-are-now-returned-as-null)

  #### Unknown Keys Will Fail Validation

  Previously, our endpoints used to only validate against the expected keys in both request body parameters as well as query parameters resulting in some ambiguity between incorrect behavior and invalid inputs. Going forward, to improve the developer experience we will be raising validation errors if keys that are not supported by our API are passed in to requests.

  <Info>
    To safely migrate to `2021-08-16`, we recommend thoroughly testing your API calls against the `2021-08-16` version, to see if you get any validation errors due to this change. If you do, remove any parameters that are rejected due to unknown keys.
  </Info>

  #### Changes to Array Rollup Property Types

  Starting with the Notion-Version header `2021-08-16`, we are introducing a change to the response for rollup properties on a page which are arrays. Number and date rollups are unaffected. Specifically, the `type` of elements within an array rollup has been made consistent with property types across other API endpoints:

  | Before           | After               |
  | ---------------- | ------------------- |
  | `type: "file"`   | `type: "files"`     |
  | `type: "text"`   | `type: "rich_text"` |
  | `type: "person"` | `type: "people"`    |

  An example rollup property value for an array of rich text values, using Notion-Version `2021-08-16`:

  <CodeGroup>
    ```json JSON theme={null}
    {
      "properties": {
        "sample text array rollup": {
          "id": "NXTh",
          "type": "rollup",
          "rollup": {
            "type": "array",
            "array": [
              {
                "type": "rich_text",
                "rich_text": [
                  {
                    "type": "text",
                    "text": {
                      "content": "hello world!",
                      "link": null
                    },
                    "annotations": {
                      "bold": false,
                      "italic": false,
                      "strikethrough": false,
                      "underline": false,
                      "code": false,
                      "color": "default"
                    },
                    "plain_text": "hello world!",
                    "href": null
                  }
                ]
              },
              {
                "type": "rich_text",
                "rich_text": [
                  {
                    "type": "text",
                    "text": {
                      "content": "foo bar",
                      "link": null
                    },
                    "annotations": {
                      "bold": false,
                      "italic": false,
                      "strikethrough": false,
                      "underline": false,
                      "code": false,
                      "color": "default"
                    },
                    "plain_text": "foo bar",
                    "href": null
                  }
                ]
              }
            ]
          }
        },
      }
    }
    ```
  </CodeGroup>

  #### Append Block Children returns a list of blocks

  The [Append Block Children](/reference/patch-block-children) endpoint will now return a list of the newly created [Block object](/reference/block) children.

  Previously the endpoint returned the block object of the parent block. Developers can instead use the [Retrieve a block](/reference/retrieve-a-block) endpoint to get the full block object for a specified `block_id`.

  This change allows developers to get `block_id`'s and additional information of the new blocks right after they're created. Note: only the first level block children are returned. To get sub-children, use the [Retrieve block children](/reference/get-block-children) endpoint.

  <CodeGroup>
    ```json Example response theme={null}
    {
        "object": "list",
        "results": [
           {
                "object": "block",
                "id": "9bc30ad4-9373-46a5-84ab-0a7845ee52e6",
                "created_time": "2021-03-16T16:31:00.000Z",
                "last_edited_time": "2021-03-16T16:32:00.000Z",
                "has_children": false,
                "type": "heading_2",
                "heading_2": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Lacinato kale",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "Lacinato kale",
                            "href": null
                        }
                    ]
                }
            },
            {
                "object": "block",
                "id": "7face6fd-3ef4-4b38-b1dc-c5044988eec0",
                "created_time": "2021-03-16T16:34:00.000Z",
                "last_edited_time": "2021-03-16T16:36:00.000Z",
                "has_children": false,
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Lacinato kale",
                                "link": {
                                    "url": "https://en.wikipedia.org/wiki/Lacinato_kale"
                                }
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": "Lacinato kale",
                            "href": "https://en.wikipedia.org/wiki/Lacinato_kale"
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": " is a variety of kale with a long tradition in Italian cuisine, especially that of Tuscany. It is also known as Tuscan kale, Italian kale, dinosaur kale, kale, flat back kale, palm tree kale, or black Tuscan palm.",
                                "link": null
                            },
                            "annotations": {
                                "bold": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false,
                                "code": false,
                                "color": "default"
                            },
                            "plain_text": " is a variety of kale with a long tradition in Italian cuisine, especially that of Tuscany. It is also known as Tuscan kale, Italian kale, dinosaur kale, kale, flat back kale, palm tree kale, or black Tuscan palm.",
                            "href": null
                        }
                    ]
                }
            }
        ],
        "next_cursor": null,
        "has_more": false
    }
    ```
  </CodeGroup>

  #### Property IDs are now URL Safe

  Endpoints that return property IDs as part of the response body will now return new URL safe encoded property IDs. Any request that uses property IDs (such as [Update a database](/reference/update-a-database) or [Update a page](/reference/patch-page)) should use the new URL safe ID.

  This ensures all property IDs can be referenced in the URL of any new endpoints moving forward.

  | Before  | After    |
  | ------- | -------- |
  | `DoS\`  | `DoS%5C` |
  | `title` | `title`  |
  | `vEKn`  | `vEKn`   |

  #### Empty database properties are now returned as `null`

  Previously, empty properties of date, email, number, and rollup types were omitted from the page response. Now, these empty properties are returned with `null` values.

  <CodeGroup>
    ```json Example page response with empty properties theme={null}
    {
        "object": "page",
        "id": "a8b7e96d-22ce-44d8-991f-6c4535af6608",
        "created_time": "2021-05-12T06:16:00.000Z",
        "last_edited_time": "2021-08-12T21:36:00.000Z",
        "cover": null,
        "icon": null,
        "parent": {
            "type": "database_id",
            "database_id": "70ff0393-6b40-4e76-afc4-4a26a9aa1606"
        },
        "archived": false,
        "properties": {
            "MyDate": {
                "id": "GZT~",
                "type": "date",
                "date": null
            },
            "Description": {
                "id": "RPld",
                "type": "rich_text",
                "rich_text": []
            },
            "Food group": {
                "id": "W_iA",
                "type": "select",
                "select": null
            },
            "myRollup": {
                "id": "%5Eu%3EC",
                "type": "rollup",
                "rollup": {
                    "type": "array",
                    "array": []
                }
            },
            "MyRelation": {
                "id": "_pL%3A",
                "type": "relation",
                "relation": []
            },
            "Price": {
                "id": "dPVb",
                "type": "number",
                "number": null
            },
            "MyMultiSelect": {
                "id": "%7B%40%5Co",
                "type": "multi_select",
                "multi_select": null
            },
        },
        "url": "https://notion.so/a8b7e96d22ce44d8991f6c4535af6608"
    }
    ```
  </CodeGroup>

  ## August 20, 2021

  ### Formula properties can now be created in databases

  When [creating](/reference/create-a-database) or [updating](/reference/update-a-database) databases, you can now add `formula` property types.

  #### Example request

  <CodeGroup>
    ```bash cURL theme={null}
    curl --location --request POST 'https://api.notion.com/v1/databases/' \
    --header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
    --header 'Content-Type: application/json' \
    --header 'Notion-Version: 2021-05-13' \
    --data '{
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                }
            }
        ],
        "properties": {
            "Name": {
                "title": {}
            },
            "Description": {
                "rich_text": {}
            },
            "In stock": {
                "checkbox": {}
            },
            "Price": {
                "number": {
                    "format": "dollar"
                }
            },
            "Cost of next trip": {
                "formula": {
                    "expression": "if(prop(\"In stock\"), 0, prop(\"Price\"))"
                }
            }
        }
    }'
    ```
  </CodeGroup>

  #### Example response

  <CodeGroup>
    ```json JSON theme={null}
    {
        "object": "database",
        "id": "c23f0085-a061-41c0-b8a6-cbe14d15a4de",
        "created_time": "2021-08-20T16:08:00.000Z",
        "last_edited_time": "2021-08-20T16:08:00.000Z",
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                },
                "annotations": {
                    "bold": false,
                    "italic": false,
                    "strikethrough": false,
                    "underline": false,
                    "code": false,
                    "color": "default"
                },
                "plain_text": "Grocery List",
                "href": null
            }
        ],
        "properties": {
            "Cost of next trip": {
                "id": "Rbq\\",
                "name": "Cost of next trip",
                "type": "formula",
                "formula": {
                    "expression": "if(prop(\"In stock\"), 0, prop(\"Price\"))"
                }
            },
            "In stock": {
                "id": "\\JwC",
                "name": "In stock",
                "type": "checkbox",
                "checkbox": {}
            },
            "Description": {
                "id": "`}HT",
                "name": "Description",
                "type": "rich_text",
                "rich_text": {}
            },
            "Price": {
                "id": "u|<{",
                "name": "Price",
                "type": "number",
                "number": {
                    "format": "dollar"
                }
            },
            "Name": {
                "id": "title",
                "name": "Name",
                "type": "title",
                "title": {}
            }
        },
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        }
    }
    ```
  </CodeGroup>

  ## August 11, 2021

  ### OAuth token response now includes workspace ID and owner info

  We now return a `workspace_id` field and an `owner` in the [token response](/guides/get-started/authorization) at the very end of the OAuth authorization flow.

  `workspace_id` is the ID of the workspace where the integration was authorized. As a reminder, this is **not** intended to be unique across tokens; in future iterations of our authorization flow users may be able to authorize your integration multiple times in the same workspace.

  `owner` contains information about who can view and share the integration. Because all integrations today can be viewed and shared by all members in the space, `owner` is just an object that looks like `{ "workspace": true }` for now.

  To summarize, the OAuth token response now looks like this:

  | Field              | Type     | Description                                                                                                             | Not null |
  | ------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------- | -------- |
  | `"access_token"`   | `string` | An access token used to authorize requests to the Notion API.                                                           | ✅        |
  | `"workspace_id"`   | `string` | The ID of the workspace where this authorization took place.                                                            | ✅        |
  | `"workspace_name"` | `string` | A human-readable name which can be used to display this authorization in UI.                                            |          |
  | `"workspace_icon"` | `string` | A URL to an image which can be used to display this authorization in UI.                                                |          |
  | `"bot_id"`         | `string` | An identifier for this authorization.                                                                                   | ✅        |
  | `"owner"`          | `object` | An object containing information about who can view and share this integration. Always `{ "workspace": true }` for now. | ✅        |

  ## August 11, 2021

  ### Update existing databases with PATCH /v1/databases

  You can now use the Notion API to [update databases](/reference/update-a-database)!

  Supported updates are:

  * renaming the database
  * adding and removing properties
  * renaming properties
  * updating property types.

  Note that updating the `name` and `color` select and multi select options is not supported.

  #### Example request

  <CodeGroup>
    ```bash cURL expandable theme={null}
    curl --location --request PATCH 'https://api.notion.com/v1/databases/668d797c-76fa-4934-9b05-ad288df2d136' \
    --header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
    --header 'Content-Type: application/json' \
    --header 'Notion-Version: 2021-07-27' \
    --data '{
        "title": [
            {
                "text": {
                    "content": "Today'\''s grocery list"
                }
            }
        ],
        "properties": {
            "+1": null,
            "Photo": {
                "url": {}
            },
            "Store availability": {
                "multi_select": {
                    "options": [
                        {
                            "name": "Duc Loi Market"
                        },
                        {
                            "name": "Rainbow Grocery"
                        },
                        {
                            "name": "Gus'\''s Community Market"
                        },
                        {
                            "name": "The Good Life Grocery",
                            "color": "orange"
                        }
                    ]
                }
            }
        }
    }'
    ```
  </CodeGroup>

  #### Example response

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "object": "database",
      "id": "668d797c-76fa-4934-9b05-ad288df2d136",
      "created_time": "2020-03-17T19:10:00.000Z",
      "last_edited_time": "2021-08-11T17:26:00.000Z",
      "parent": {
        "type": "page_id",
        "page_id": "48f8fee9-cd79-4180-bc2f-ec0398253067"
      },
      "title": [
        {
          "type": "text",
          "text": {
            "content": "Today'\''s grocery list",
            "link": null
          },
          "annotations": {
            "bold": false,
            "italic": false,
            "strikethrough": false,
            "underline": false,
            "code": false,
            "color": "default"
          },
          "plain_text": "Today'\''s grocery list",
          "href": null
        }
      ],
      "properties": {
        "Name": {
          "id": "title",
          "type": "title",
          "title": {}
        },
        "Description": {
          "id": "J@cS",
          "type": "rich_text",
          "rich_text": {}
        },
        "In stock": {
          "id": "{xY`",
          "type": "checkbox",
          "checkbox": {}
        },
        "Food group": {
          "id": "TJmr",
          "type": "select",
          "select": {
            "options": [
              {
                "id": "96eb622f-4b88-4283-919d-ece2fbed3841",
                "name": "🥦Vegetable",
                "color": "green"
              },
              {
                "id": "bb443819-81dc-46fb-882d-ebee6e22c432",
                "name": "🍎Fruit",
                "color": "red"
              },
              {
                "id": "7da9d1b9-8685-472e-9da3-3af57bdb221e",
                "name": "💪Protein",
                "color": "yellow"
              }
            ]
          }
        },
        "Price": {
          "id": "cU^N",
          "type": "number",
          "number": {
            "format": "dollar"
          }
        },
        "Cost of next trip": {
          "id": "p:sC",
          "type": "formula",
          "formula": {
            "value": "if(prop(\"In stock\"), 0, prop(\"Price\"))"
          }
        },
        "Last ordered": {
          "id": "]\\R[",
          "type": "date",
          "date": {}
        },
        "Meals": {
          "type": "relation",
          "relation": {
            "database": "668d797c-76fa-4934-9b05-ad288df2d136",
            "synced_property_name": null
          }
        },
        "Number of meals": {
          "id": "Z\\Eh",
          "type": "rollup",
          "rollup": {
            "rollup_property_name": "Name",
            "relation_property_name": "Meals",
            "rollup_property_id": "title",
            "relation_property_id": "mxp^",
            "function": "count"
          }
        },
        "Store availability": {
          "type": "multi_select",
          "multi_select": {
            "options": [
              [
                {
                  "id": "d209b920-212c-4040-9d4a-bdf349dd8b2a",
                  "name": "Duc Loi Market",
                  "color": "blue"
                },
                {
                  "id": "70104074-0f91-467b-9787-00d59e6e1e41",
                  "name": "Rainbow Grocery",
                  "color": "gray"
                },
                {
                  "id": "6c3867c5-d542-4f84-b6e9-a420c43094e7",
                  "name": "Gus's Community Market",
                  "color": "yellow"
                },
                {
    							"id": "a62fbb5f-fed4-44a4-8cac-cba5f518c1a1",
                  "name": "Good life grocery",
                  "color": "orange"
               }
              ]
            ]
          }
        }
        "Photo": {
          "id": "aTIT",
          "type": "url",
          "url": {}
        }
      }
    }
    ```
  </CodeGroup>
</Update>

<Update label="August 3, 2021">
  ### Retrieve and update blocks with GET and PATCH /v1/blocks/:id

  You can now retrieve and update block objects with the Notion API! The `PATCH` endpoint currently supports updating `paragraph`, `heading_1`, `heading_2`, `heading_3`, `bulleted_list_item`, `numbered_list_item`, `toggle` and `to_do` blocks.

  #### Retrieve a Block

  The [Retrieve a Block](/reference/retrieve-a-block) endpoint returns a [Block Object](/reference/block).

  <CodeGroup>
    ```bash Example GET request theme={null}
    curl 'https://api.notion.com/v1/blocks/9bc30ad4-9373-46a5-84ab-0a7845ee52e6' \
      -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
      -H 'Notion-Version: 2021-05-13'
    ```
  </CodeGroup>

  <CodeGroup>
    ```json Example response expandable theme={null}
    {
      "object": "block",
      "id": "9bc30ad4-9373-46a5-84ab-0a7845ee52e6",
      "created_time": "2021-03-16T16:31:00.000Z",
      "last_edited_time": "2021-03-16T16:32:00.000Z",
      "has_children": false,
      "type": "to_do",
      "to_do": {
        "text": [
          {
            "type": "text",
            "text": {
              "content": "Lacinato kale",
              "link": null
            },
            "annotations": {
              "bold": false,
              "italic": false,
              "strikethrough": false,
              "underline": false,
              "code": false,
              "color": "default"
            },
            "plain_text": "Lacinato kale",
            "href": null
          }
        ],
        "checked": false
      }
    }
    ```
  </CodeGroup>

  #### Update a Block

  The new `PATCH` `/v1/blocks/:id` endpoint supports updating block content (the properties within the block type object) and returns the updated [Block Object](/reference/block), same as the `GET` endpoint shown above. See the [Update a Block](/reference/update-a-block) documentation for more detail.

  <CodeGroup>
    ```bash Example PATCH request theme={null}
    curl https://api.notion.com/v1/blocks/9bc30ad4-9373-46a5-84ab-0a7845ee52e6 \
      -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
      -H "Content-Type: application/json" \
      -H "Notion-Version: 2021-05-13" \
      -X PATCH \
      --data '{
      "to_do": {
        "text": [{
          "text": { "content": "Lacinato kale" }
          }],
        "checked": false
      }
    }'
    ```
  </CodeGroup>
</Update>

<Update label="July 26, 2021">
  ### Number properties now support more currency formats

  The number property type in databases now supports additional currency options.

  The new options are:

  * "hong\_kong\_dollar"
  * "new\_zealand\_dollar"
  * "krona"
  * "norwegian\_krone"
  * "mexican\_peso"
  * "rand"
  * "new\_taiwan\_dollar"
  * "danish\_krone"
  * "zloty"
  * "baht"
  * "forint"
  * "koruna"
  * "shekel"
  * "chilean\_peso"
  * "philippine\_peso"
  * "dirham"
  * "colombian\_peso"
  * "riyal"
  * "ringgit"
  * "leu"

  This impacts the [number configuration of databases](/reference/property-schema-object#number-configuration).
</Update>

<Update label="July 22, 2021">
  ### OAuth improvements

  We've made improvements to the OAuth flow to make it easier to use.

  **We now show the page picker on reauthorization.** Just like before, the user who initially authorized an integration can reauthorize by going through OAuth a second time. The page picker step will remember which pages have already been shared with the integration, if any, and let users share or un-share additional pages.

  **Users can search for pages to share with an integration.** Previously, users could only select pages at the top level of the Workspace, Shared section, or Private pages section to share with an integration, but we've added a search bar so users can search for and select any page in their workspace.

  We also updated the page picker to only show pages for which the user has Full Access permission. Previously, the page picker show any pages for which the user had at least Can View permission, but would show an error when they tried to give the permission access to those pages.

  Other OAuth behavior has not changed: only admins can go through OAuth, and only the original person originally added an integration via OAuth can go through the flow again.

  <Frame caption="The search bar now lets you search for and select nested pages to share with an integration.">
    <img src="https://mintcdn.com/notion-demo/9OFhQspLr8njnajd/images/docs/15c452e-oauth_improvements.png?fit=max&auto=format&n=9OFhQspLr8njnajd&q=85&s=3279ba235d3640e80fe9a0bac2b9b8ff" width="1164" height="1358" data-path="images/docs/15c452e-oauth_improvements.png" />
  </Frame>

  <Frame caption="Once selected, any nested pages appear in the &#x22;Manually Added&#x22; section.">
    <img src="https://mintcdn.com/notion-demo/9OFhQspLr8njnajd/images/docs/63ac8e6-oauth2.png?fit=max&auto=format&n=9OFhQspLr8njnajd&q=85&s=73927dbfab4f1b327dd80d5235c4b34f" width="1134" height="1356" data-path="images/docs/63ac8e6-oauth2.png" />
  </Frame>
</Update>

<Update label="July 21, 2021">
  ### Database property objects now include the property name

  [Database property objects](/reference/property-schema-object#database-properties) now include the field `name` with the property name as it appears in Notion.
</Update>

<Update label="July 15, 2021">
  ### Rollup property functions now include show\_original

  The `function` `show_original` has now been added to [rollup database property objects](/reference/property-schema-object#rollup-configuration). This fixes a bug where rollup properties were omitted if the calculation was "Show Original".
</Update>

<Update label="July 13, 2021">
  ### Create new databases with POST /v1/databases

  You can now use the Notion API to [create a database](/reference/create-a-database) as a subpage of an existing page. Currently supported property types are `"title"`, `"rich_text"`, `"number"`, `"select"`, `"multi_select"`, `"date"`, `"people"`, `"files"`, `"checkbox"`, `"url"`, `"email"`, `"phone_number"`, `"created_time"`, `"created_by"`, `"last_edited_time"`, `"last_edited_by"`.

  #### Example request

  <CodeGroup>
    ```bash cURL expandable theme={null}
    curl --location --request POST 'https://api.notion.com/v1/databases/' \
    --header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
    --header 'Content-Type: application/json' \
    --header 'Notion-Version: 2021-05-13' \
    --data '{
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                }
            }
        ],
        "properties": {
            "Name": {
                "title": {}
            },
            "Description": {
                "rich_text": {}
            },
            "In stock": {
                "checkbox": {}
            },
            "Food group": {
                "select": {
                    "options": [
                        {
                            "name": "🥦Vegetable",
                            "color": "green"
                        },
                        {
                            "name": "🍎Fruit",
                            "color": "red"
                        },
                        {
                            "name": "💪Protein",
                            "color": "yellow"
                        }
                    ]
                }
            },
            "Price": {
                "number": {
                    "format": "dollar"
                }
            },
            "Last ordered": {
                "date": {}
            },
            "Store availability": {
                "type": "multi_select",
                "multi_select": {
                    "options": [
                        {
                            "name": "Duc Loi Market",
                            "color": "blue"
                        },
                        {
                            "name": "Rainbow Grocery",
                            "color": "gray"
                        },
                        {
                            "name": "Nijiya Market",
                            "color": "purple"
                        },
                        {
                            "name": "Gus'\''s Community Market",
                            "color": "yellow"
                        }
                    ]
                }
            },
            "+1": {
                "people": {}
            },
            "Photo": {
                "files": {}
            }
        }
    }'
    ```
  </CodeGroup>

  #### Example response

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
        "object": "database",
        "id": "bc1211ca-e3f1-4939-ae34-5260b16f627c",
        "created_time": "2021-07-08T23:50:00.000Z",
        "last_edited_time": "2021-07-08T23:50:00.000Z",
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                },
                "annotations": {
                    "bold": false,
                    "italic": false,
                    "strikethrough": false,
                    "underline": false,
                    "code": false,
                    "color": "default"
                },
                "plain_text": "Grocery List",
                "href": null
            }
        ],
        "properties": {
            "+1": {
                "id": "PNEQ",
                "type": "people",
                "people": {}
            },
            "In stock": {
                "id": "V>GQ",
                "type": "checkbox",
                "checkbox": {}
            },
            "Price": {
                "id": "V@]u",
                "type": "number",
                "number": {
                    "format": "dollar"
                }
            },
            "Description": {
                "id": "V}lX",
                "type": "rich_text",
                "rich_text": {}
            },
            "Last ordered": {
                "id": "eVnV",
                "type": "date",
                "date": {}
            },
            "Store availability": {
                "id": "s}Kq",
                "type": "multi_select",
                "multi_select": {
                    "options": [
                        {
                            "id": "cb79b393-d1c1-4528-b517-c450859de766",
                            "name": "Duc Loi Market",
                            "color": "blue"
                        },
                        {
                            "id": "58aae162-75d4-403b-a793-3bc7308e4cd2",
                            "name": "Rainbow Grocery",
                            "color": "gray"
                        },
                        {
                            "id": "22d0f199-babc-44ff-bd80-a9eae3e3fcbf",
                            "name": "Nijiya Market",
                            "color": "purple"
                        },
                        {
                            "id": "0d069987-ffb0-4347-bde2-8e4068003dbc",
                            "name": "Gus's Community Market",
                            "color": "yellow"
                        }
                    ]
                }
            },
            "Photo": {
                "id": "yfiK",
                "type": "files",
                "files": {}
            },
            "Food group": {
                "id": "|JKd",
                "type": "select",
                "select": {
                    "options": [
                        {
                            "id": "6d4523fa-88cb-4ffd-9364-1e39d0f4e566",
                            "name": "🥦Vegetable",
                            "color": "green"
                        },
                        {
                            "id": "268d7e75-de8f-4c4b-8b9d-de0f97021833",
                            "name": "🍎Fruit",
                            "color": "red"
                        },
                        {
                            "id": "1b234a00-dc97-489c-b987-829264cfdfef",
                            "name": "💪Protein",
                            "color": "yellow"
                        }
                    ]
                }
            },
            "Name": {
                "id": "title",
                "type": "title",
                "title": {}
            }
        },
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        }
    }
    ```
  </CodeGroup>
</Update>

<Update label="July 7, 2021">
  ### User mentions can only be of people

  To be consistent with the Notion application, only users of type "people" can be mentioned in rich text objects or in people properties of databases. Trying to include users of type "bot" will return a validation error. Existing mentions of bot users is unaffected.
</Update>

<Update label="July 1, 2021">
  ### Page objects now contain url

  [Page objects](/reference/page) now return the web address of the page in the `url` key.

  <CodeGroup>
    ```json JSON expandable theme={null}
    {
      "object": "page",
      "id": "251d2b5f-268c-4de2-afe9-c71ff92ca95c",
    	"created_time": "2020-03-17T19:10:04.968Z",
    	"last_edited_time": "2020-03-17T21:49:37.913Z",
      "parent": {
        "type": "database_id",
        "database_id": "48f8fee9-cd79-4180-bc2f-ec0398253067"
      },
      "archived": false,
      "url": "https://www.notion.so/Avocado-251d2b5f268c4de2afe9c71ff92ca95c",
      "properties": {
        "Name": {
          "id": "title",
          "type": "title",
          "title": [
            {
              "type": "text",
              "text": {
                "content": "Avocado",
                "link": null
              },
              "annotations": {
                "bold": false,
                "italic": false,
                "strikethrough": false,
                "underline": false,
                "code": false,
                "color": "default"
              },
              "plain_text": "Avocado",
              "href": null
            }
          ]
        }
      }
    }
    ```
  </CodeGroup>

  This impacts endpoints that return page object: the [pages](/reference/page) endpoints and [query database](/reference/post-database-query) endpoint.
</Update>

<Update label="June 28, 2021">
  ### Last edited and created time properties are now rounded to the nearest minute

  Starting July 1st, the `last_edited_time` and `created_time` properties will be rounded down to the closest minute for `page`, `database` , and `block` objects. Previously, this behavior was inconsistent with some times being rounded and others not.
</Update>

<Update label="June 23, 2021">
  ### Database objects now return parent

  Database objects now return a [parent property](/reference/parent-object#database-parent). Databases can have pages or workspaces as parents.

  <CodeGroup>
    ```json JSON theme={null}
    {
      "parent": {
        "type": "page_id",
        "page_id": "b8595b75-abd1-4cad-8dfe-f935a8ef57cb"
    }
    ```
  </CodeGroup>

  ### Other Improvements and Fixes

  * Inline database mentions are now included in [rich\_text mention](/reference/rich-text#database-mention-type-object) responses.
  * When an integration does not have access to a [page or database mention](/reference/rich-text#page-mention-type-object), we will no longer completely omit the mention. The mention will be returned with just the ID but without detailed information (title will appear as "Untitled" and annotations will be default).
  * When integrations are added to pages inside collections they can now always update page properties, even when the integration does not have access to the parent database. However, integrations will not be able to add new [select](/reference/page-property-values#select) or [multi-select](/reference/page-property-values#multi-select) properties through the create or update page endpoints without the ability to edit the database parent.
</Update>

<Update label="June 15, 2021">
  ### Select values can now be dynamically created via Create and Update Page endpoints + other updates since public beta launch

  You can now dynamically create new options for [Select](/reference/property-schema-object#select-configuration) or [Multi-Select properties](/reference/property-schema-object#multi-select-configuration) when using the [Create Page](/reference/post-page) and [Update Page](/reference/patch-page) endpoints. When specifying an option that does not exist in the database schema already, the option will now be created and the database schema updated accordingly.

  <CodeGroup>
    ```json JSON theme={null}
    {
      "properties": {
        "Food group": {
          "multi_select": [{"name": "Vegetable"},{"name": "Fruit"}]
        }
      }
    }
    ```
  </CodeGroup>

  In the above [property values](/reference/page-property-values) example: Previously, if either "Vegetable" or "Fruit" did not already exist as an option in the database schema, an error would be returned that these are not valid Select options. Now, these options will be created dynamically.

  **Bug Fixes**

  * The title property of a page can be set, and a page can be archived or un-archived, even when the page does not belong to a database.
  * [Retrieving pages](/reference/post-page) that are shared with an integration, but where the page's parent is not shared, no longer erroneously returns a 404.

  **Other Changes**

  * [Search endpoint](/reference/post-search) now returns untitled pages.
  * Applies to [version 2021-05-13](/reference/versioning) and later only: The [Query Database](/reference/post-database-query) endpoint no longer accepts query parameters – these should be sent as body parameters.
</Update>

<Update label="May 19, 2021">
  ### "Notion-Version" header will be required starting June 1, 2021

  The Notion API has recommended using an explicit version to every HTTP request, using the `Notion-Version` header. **For integrations created after June 1, 2021 an explicit version on every request will become required**. After July 1, 2021, integrations created before June 1, 2021 will also have the same requirement. Today, the most recent version is `"2021-05-13"`.

  #### Is my integration affected? What should I do to update?

  This requirement will not break your existing integration; however, we will start enforcing this requirement for all API requests on July 1st. Starting July 1st, if you don't send the Notion-Version header with your Notion API calls, you will get a [`"missing_version"` error](/reference/errors). Learn more about how the Notion API [handles versioning](/reference/versioning).

  If you've been using examples copied from documentation or example code since the public beta, including using the [Notion SDK for JavaScript](https://github.com/makenotion/notion-sdk-js), your existing code should continue to work as expected.

  Otherwise, please make one of the two following changes before July 1:

  1. Add `Notion-Version: 2021-05-11` in the header when making requests (no other code change is needed).
  2. **Recommended**: Add `Notion-Version: 2021-05-13` in the header when making requests. Making this change will move you to our newest version which includes the following breaking change.

  #### Breaking changes in version `2021-05-13`

  The `type` of [property value objects](/reference/page-property-values) for rich text properties has changed from `"text"` to `"rich_text"`.

  When [creating pages](/reference/post-page) and [updating page properties](/reference/patch-page), update page property values that are rich text to use the key `rich_text` instead of `text`. Similarly when [retrieving a page](/reference/post-page), rich text properties will be returned with the `type` `"rich_text"` instead of `"text"`.

  This change helps distinguish between the property type, and the inner text values of [rich text object](/reference/rich-text), which have the key `text`.

  To illustrate this change, here is an example of how the [page object](/reference/page)'s `properties` appear before and after:

  <CodeGroup>
    ```js JavaScript theme={null}
    // Before (in unversioned requests and responses)
    {
      "object": "page",
      "properties": {
        "Description": {
          "type": "text",
          "text": [
            {
              "type": "text",
              "text": { "content": "Hello World" }
            }
          ]
        }
      }
      /* remaining details omitted */
    }
    ```
  </CodeGroup>

  <CodeGroup>
    ```js JavaScript theme={null}
    // After (in requests and responses with version 2021-05-13)
    {
      "object": "page",
      "properties": {
        "Description": {
          "type": "rich_text",
          "rich_text": [
            {
              "type": "text",
              "text": { "content": "Hello World" }
            }
          ]
        }
      }
      /* remaining details omitted */
    }
    ```
  </CodeGroup>
</Update>

<Update label="May 18, 2021">
  ### Initial users may reauthorize a public integration using OAuth

  Public integrations use OAuth to [request authorization from a user](/guides/get-started/authorization) before being added to a Notion workspace. Previously, once an integration was added to a workspace, no users were able to reauthorize the same integration in that workspace. This change allows the user who initially added the integration to complete the authorization flow more than once. This improvement helps integrations avoid a potential dead end in user flows.

  Integrations do not need to make any updates to take advantage of this new capability. An integration may simply link or redirect a user to the authorization URL, the same as the first authorization. During reauthorization the user will not see the page picker. The access token received at the end of reauthorization will be the same as the initial access token. This capability is available immediately.

  Please be aware that other previous limitations still exist. Only users with admin access level in a workspace can add an integration. Integrations can only be added to a workspace by one user.
</Update>

<Update label="May 13, 2021">
  ### Hello world, the Notion API is now in public beta

  The Notion API is now available for all developers to explore and build upon. Integrations built on the API are available to all Notion users, on free or paid plans.

  In this public beta release, you'll find many of the fundamental parts of Notion: reading and writing to pages, working with users, and the deep and powerful world of Notion databases. The API itself offers foundational features such as authorization, pagination, limits, and more. This is enough to build many interesting integrations we've heard Notion users are excited to use. We're excited to see what you'll build for all of us. [→ Get started](/guides/get-started/overview)

  Our goal is to establish that the Notion API is robust, easy to use, and trustworthy. In public beta, we’ll continue to add new features and making significant changes based on your feedback. Once the most important improvements are included, the API will transition from public beta to general availability. you’ll have everything you need to build integrations teams and businesses can depend on.

  A special thanks to the all developers who experimented, explored, and shared their ideas with us - both in the private beta and those following along.
</Update>

<Update label="May 4, 2021">
  ### Public integration type extends access to multiple workspaces using OAuth

  The Notion API has added a new integration type: Public OAuth integrations. If you're building a product or service for Notion users outside your own team - public integrations are for developers like you.

  In order to create and configure an integration, its type, name, avatar, and other related settings, the <a href={developerConnectionsUrl}>My integrations</a> page is now available.

  Public integrations use OAuth to request permission to access pages and databases in new workspaces. Once the user accepts, the integration can receive a separate access token for resources in the user's workspace.

  Existing integrations are now known as internal integrations. We no longer call the bearer token you previously used an API Key. It's now known as an integration token. You can keep your bearer token around - it will continue to work just the same.

  Learn how to implement these changes in the [authorization guide](/guides/get-started/authorization).
</Update>

<Update label="May 3, 2021">
  ### Search is now available in the API

  Using the new [search endpoint](/reference/post-search), you can query all pages and databases users have shared with your integration.

  The query you provide filters results by matching against the page title. The results also include matches against subpages of pages users have shared with your integration. This endpoint can be helpful when onboarding a new user and trying to find the page they just shared with your integration.

  We recommend transitioning away from using the [list databases endpoint](/reference/get-databases). The search endpoint provides all the same functionality - and more.
</Update>
