import sdmx


class ImfClient:
    """A high-level SDMX client for accessing IMF data."""

    def __init__(self):
        self.client = sdmx.Client(source=self.SOURCE_ID)
        self.dfds = []
        self.dsds = []

    # When querying for data, every key should be * except for (frequency = annual) and (type of transformation = index)
    # AKA we want the raw yearly data
    # dsd.dimensions[0].concept_identity.core_representation.enumerated.items.keys()
    # TODO: Find a way to specify the language for localization (English) to reduce the response size (stop giving me every string in every language in the world)
    def download(self):
        for dfd in self.ifs_dfds():
            dsd = self.dsd(dfd)
            dims = dsd.dimensions.components
            print(dfd.name, dims)
            # TODO: Determine which dimensions I care about (the ones that decide the shape of the data instead of filtering it).
            # FREQUENCY=ANNUAL, TYPE_OF_TRANFORMATION=IX,
        return

        frequency = self.frequency_code("Annual")
        if frequency is None:
            raise ValueError("Unsupported data frequency: Annual")

        flows = list(self.ifs_dataflows())
        for i, flow in enumerate(flows):
            logger.info(
                f"Getting data from dataflow ({i}/{len(flows)}): {flow.name}",
            )
            msg = self.client.data(
                context="dataflow",
                agency_id=flow.maintainer.id,
                resource_id="TODO",
                key="TODO",
            )
            data = sdmx.to_pandas(msg)

        country = const.WILDCARD
        indicator = "CPI"

        message = self.client.data(
            context="dataflow",
            agency_id=self.AGENCY_ID,
            resource_id="CPI",
            key=f"{country}.{indicator}.*.IX.{frequency}",
        )

    def frequency_code(self, name):
        """Return the query code for a valid data frequency (e.g. "A" for "Annual")."""
        msg = self.client.codelist(
            agency_id=self.AGENCY_ID,
            resource_id=const.RESOURCE_ID_CODELIST_FREQUENCY,
        )
        cl_freq = msg.codelist[const.RESOURCE_ID_CODELIST_FREQUENCY]
        for code, meta in cl_freq.items.items():
            loc = meta.name.localizations
            if "en" in loc and loc["en"].lower() == name.lower():
                return code

        return None

    def ifs_dfds(self):
        """Yield all IFS dataflow definitions."""
        msg = self.client.dataflow()
        for id in self.IFS_DATAFLOW_IDS:
            try:
                yield msg.dataflow[id]
            except IndexError:
                logging.warn(f"No DFD found for IFS dataflow ID: {id}")
                continue

    def dsd(self, dfd):
        """Return the DSD corresponding to a DFD."""
        msg = self.client.dataflow(resource=dfd, references="none")
        return msg.structure[dfd.structure.id]

    SOURCE_ID = "IMF_DATA"
    AGENCY_ID = "IMF"
    IFS_DATAFLOW_IDS = [
        # Balance of Payments
        "BOP",
        # Balance of Payments and International Investment Position Statistics, World and Country Group Aggregates
        # TODO: Is this still IFS?
        "BOP_AGG",
        # Consumer Price Index
        "CPI",
        # Consumer Price Index, World and Country Aggregates
        # TODO: Is this still IFS?
        "CPI_WCA",
        # Effective Exchange Rate
        "EER",
        # Exchange Rates
        "ER",
        # International Investment Position
        "IIP",
        # Currency Composition of the International Investment Position
        # TODO: Is this still IFS?
        "IIPCC",
        # International Liquidity
        "IL",
        # International Trade in Goods
        "ITG",
        # International Trade in Goods, World and Country Aggregates
        "ITG_WCA",
        # Labor Statistics
        "LS",
        # Monetary and Financial Statistics, Central Bank Data
        "MFS_CBS",
        # Monetary and Financial Statistics, Depository Corporations
        "MFS_DC",
        # Monetary and Financial Statistics, Financial Corporations
        "MFS_FC",
        # Monetary and Financial Statistics, Financial Market Prices
        "MFS_FMP",
        # Monetary and Financial Statistics, Interest Rate
        # TODO: Is this still IFS?
        "MFS_IR",
        # Monetary and Financial Statistics, Monetary Aggregates
        # TODO: Is this still IFS?
        "MFS_MA",
        # Monetary and Financial Statistics, Non-Standard Data
        "MFS_NSRF",
        # Monetary and Financial Statistics, Other Depository Corporations
        "MFS_ODC",
        # Monetary and Financial Statistics, Other Financial Corporations
        "MFS_OFC",
        # National Economic Accounts, Annual Data
        "ANEA",
        # National Economic Accounts, Quarterly Data
        "QNEA",
        # Producer Price Index
        "PPI",
        # Production Indexes
        "PI",
        # Production Indexes, World and Country Group Aggregates
        "PI_WCA",
        # Quarterly Government Finance Statistics
        "QGFS",
        # Quarterly Gross Domestic Product, World and Country Aggregates
        "QGDP_WCA",
        # Special Purpose Entities
        "SPE",
    ]
    KEYS = {
        "FREQ": "A",
        "TYPE_OF_TRANFORMATION": "IX",
    }
