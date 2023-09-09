from . import *


class CollectionNotFound(Exception):
    ...


class Database:
    def __init__(self):
        self.__cache: dict[str, dict] = {}  # {collection: {id: document object}}

        self.collections = {
            'level': Level,
            'levels': Level,
            'lvl': Level,
            'lvls': Level,

            'mute': Mute,
            'mutes': Mute,

            'marriage': Marriage,
            'marriages': Marriage,

            'miscellaneous': Misc,
            'misc': Misc,
            'miscs': Misc,

            'intro': Intros,
            'intros': Intros,

            'birthday': Birthday,
            'birthdays': Birthday,
            'bday': Birthday,
            'bdays': Birthday,

            'afk': AFK,
            'afks': AFK,

            'giveaway': Giveaway,
            'giveaways': Giveaway,
            'gw': Giveaway,
            'gws': Giveaway
        }

        self.all_collections = [
            Level, Mute, Marriage, Misc, Birthday, AFK, Giveaway
        ]

    async def add_to_cache(
            self,
            collection=None
    ):
        """|coro|

        Add to cache.

        Parameters
        ----------
            collection: the collection object (e.g: Mutes, Rules, Intro, Tags, etc...)
                The collection to cache, if `None` then it will begin caching
                all collections.
        """

        # The collection wasn't specified so loop through
        # all the collections and begin caching them.
        if collection is None:
            for col in self.all_collections:

                # We look to see if it actually is cached,
                # and if it is then delete it from cache and
                # continue with caching it again in case
                # a document was missing or if anything
                # went wrong.
                if self.__cache.get(col.__name__) is not None:
                    del self.__cache[col.__name__]

                self.__cache[col.__name__] = {}
                async for document in col.find():
                    self.__cache[col.__name__][document.pk] = document
            return

        try:
            col_name = collection.__name__
        except AttributeError:
            col_name = collection.name

        if self.__cache.get(col_name) is not None:
            del self.__cache[col_name]

        self.__cache[col_name] = {}
        async for document in collection.find():
            self.__cache[col_name][document.pk] = document

    async def find(
            self,
            collection_name: str,
            filtered: dict = None
    ):
        """|coro|

        Filter for all documents in the specified collection.

        Parameters
        ----------
            collection_name: :class:`str`
                The collection name to filter in (e.g: tags, warns, etc).

            filtered: :class:`dict`
                The filter to apply when looking up for the documents in the collection.
                If not provided returns all documents within the collection.

        Return
        -------
            A list of document objects if found else `None`.

        Raises
        ------
            :class:`CollectionNotFound` when the collection_name is wrong or not added.
        """

        # We first try and see if we can find the specified collection,
        # if we cannot then we raise `CollectionNotFound`
        collection_name = collection_name.lower()
        col = self.collections.get(collection_name)
        if col is None:
            raise CollectionNotFound(
                f'collection with the name `{collection_name}` does not exist.'
            )

        # We found the collection, so now we try to get it
        # from the cache, if the collection isn't cached then we will
        # create an empty dict in the collection's cache where
        # the documents for this collection will be stored.
        collection = self.__cache.get(col.__name__)
        if collection is None:
            await self.add_to_cache(col)

            # Since we couldn't find the documents in the cache,
            # we use the default `.find` method of the document
            # object.

            if filtered is None:
                return await col.find().to_list(500000)  # filters up to 500k docs

            return await col.find(filtered).to_list(500000)  # filters up to 500k docs

        # If no filter provided simply return all
        if filtered is None:
            return list(collection.values())

        # This is here simply to ease the process of `.find_one`
        if len(filtered) == 1 and filtered.get('_id') is not None:
            return [collection.get(filtered['_id'])]

        # Look for every doc in the cached collection and check
        # for filter matches.
        matches = []
        for doc in collection.values():
            if all(doc[key] == value for key, value in filtered.items()):
                matches.append(doc)

        return matches

    async def find_sorted(
        self,
        collection_name: str,
        sort_by: str,
        sort_type: int,
        filtered: dict = None
    ):
        """|coro|

        Returns a list of document objects but sorted.

        Parameters
        ----------
            collection_name: :class:`str`
                The collection name to filter in (e.g: tags, warns, etc).

            sort_by: :class:`str`
                What field to sort by.

            sort_type: :class:`int`
                How to sort, `1` is for ASCENDING and `0` is for DESCENDING.

            filtered: :class:`dict`
                The filter to apply in case you want to sort based on certain docs.

        Return
        ------
            A list of document objects.
        """

        documents = await self.find(collection_name, filtered)
        reverse = True if sort_type == 0 else False

        return sorted(documents, reverse=reverse, key=lambda doc: doc[sort_by])

    async def find_one(
            self,
            collection_name: str,
            filtered: dict
    ):
        """|coro|

        Finds a single document based on the filter given.

        Parameters
        ----------
            collection_name: :class:`str`
                The collection name to filter in (e.g: tags, warns, etc).

            filtered: :class:`dict`
                The filter to apply when looking up for the documents in the collection.

        Return
        ------
            The document object if found else `None`.
        """

        doc = await self.find(collection_name, filtered)
        if len(doc) == 0:
            return None
        return doc[0]

    async def get(
            self,
            collection_name: str,
            id: int = 1114756730157547622
    ):
        """|coro|

        Get a single document from the collection.

        Parameters
        ----------
            collection_name: :class:`str`
                The collection name to get the document from (e.g: tags, warns, etc).

            id: :class:`int`
                The id of the document to look-up for. Defaults to the owner id.

        Return
        ------
            The document object if found else `None`.
        """

        return await self.find_one(collection_name, {'_id': id})

    async def delete(
            self,
            collection_name: str,
            filtered: dict
    ):
        """|coro|

        Deletes documents in the given collection based on the filter.

        Parameters
        ----------
            collection_name: :class:`str`
                The collection name to get the document from (e.g: tags, warns, etc).

            filtered: :class:`dict`
                The filter to apply when looking up in the collection.
        """

        documents = await self.find(collection_name, filtered)
        collection = self.collections[collection_name.lower()]
        for document in documents:
            if document is not None:
                del self.__cache[collection.__name__][document.pk]
                await document.delete()

    async def add(self, collection_name, document):
        """|coro|

        Adds a document to the database and to the cache.

        Parameters
        ----------
            collection_name: :class:`str`
                The collection to add this document to (e.g: tags, warns, etc).

            document: doc object
                The document to add.
        """

        collection_name = collection_name.lower()
        collection = self.collections.get(collection_name)
        if collection is None:
            raise CollectionNotFound(
                f'collection with the name `{collection_name}` does not exist.'
            )

        await document.commit()
        document = await collection.get(document.pk)
        if self.__cache.get(collection.__name__) is None:
            return await self.add_to_cache(collection)

        self.__cache[collection.__name__][document.pk] = document