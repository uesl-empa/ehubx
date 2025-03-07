"""Network submodel"""

from datetime import datetime

from pyomo.core import Binary, Constraint, Model, NonNegativeReals, Reals, Set, Var

from ehubx.core import common, logging
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.net_link_data import NetLinkDirection, NetLinkId, NetworkLinks
from ehubx.data.net_tech_data import NetTechId, NetworkTechs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.model.common import calculate_crf
from ehubx.model.demand_model import PAR_BIGMGENERIC
from ehubx.model.ec_model import SET_EC
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/network"
"""String identifying the network model for logging purposes"""

SET_NETLINK: str = "S_NetLink"
"""Name of set with network link indices"""

SET_NETLINKANDEC: str = "S_NetLinkAndEc"
"""Name of set with (link, ec) tuples"""

SET_NETTECH: str = "S_NetTech"
"""Name of set with network tech indices"""

SET_NETLINKIN: str = "S_NetLinkIn"
"""Name of set with all (hub, link, ec) tuples with inputs for network
transfer"""

SET_NETLINKOUT: str = "S_NetLinkOut"
"""Name of set with all (hub, link, ec) tuples with outputs for network
transfer"""

SET_NETHUBIN: str = "S_NetHubIn"
"""Name of set with all (hub, ec) tuples with inputs for network transfer"""

SET_NETHUBOUT: str = "S_NetHubOut"
"""Name of set with all (hub, ec) tuples with outputs for network transfer"""

SET_NETTECHTUPLE: str = "S_NetTechTuple"
"""Name of set with all allowed (stage, link, net_tech) tuples"""

SET_NETTECHIN: str = "S_NetTechIn"
"""Name of set with all (stage, hub, link, net_tech) tuples with inputs for
network transfer"""

SET_NETTECHOUT: str = "S_NetTechOut"
"""Name of set with all (stage, hub, link, net_tech) tuples with outputs for
network transfer"""

VAR_NETLINKIN: str = "V_NetLinkIn"
"""Name of variable for all network input amounts at hubs per link"""

VAR_NETLINKOUT: str = "V_NetLinkOut"
"""Name of variable for all network output amounts at hubs per link"""

VAR_NETHUBIN: str = "V_NetHubIn"
"""Name of variable for all network input amounts at hubs"""

VAR_NETHUBOUT: str = "V_NetHubOut"
"""Name of variable for all network output amounts at hubs"""

VAR_NETTECHIN: str = "V_NetTechIn"
"""Name of variable for all network input amounts at hubs per link and
network tech"""

VAR_NETTECHOUT: str = "V_NetTechOut"
"""Name of variable for all network output amounts at hubs per link and
network tech"""

VAR_YNETTECHUSED: str = "V_YNetTechUsed"
"""Name of variable monitoring network tech usage"""

VAR_NETTECHCAP: str = "V_NetTechCap"
"""Name of variable for network tech capacity (contains initial capacity and
installed capacity)"""

VAR_NETTECHCAPINSTL: str = "V_NetTechCapInstl"
"""Name of variable for installed network tech capacity"""

VAR_YNETTECHCAPINSTL: str = "V_YNetTechCapInstl"
"""Name of variable monitoring whether any new network technology was
installed at all"""

VAR_NETTECHCOSTCAPEX: str = "V_NetTechCostCapex"
"""Name of variable for CAPEX costs of network technology installation"""

VAR_NETTECHCOSTOPEXCAP: str = "V_NetTechCostOpexCap"
"""Name of variable for OPEX costs for network technologies based on
capacity"""

VAR_NETTECHCOSTOPEXTRANS: str = "V_NetTechCostOpexTrans"
"""Name of variable for OPEX costs for network technologies based on
transmission amounts"""

VAR_NETTECHCOSTTOTAL: str = "V_NetTechCostTotal"
"""Name of variable for total network tech costs"""

VAR_NETTECHCO2INSTL: str = "V_NetTechCo2Instl"
"""Name of variable for embodied CO2 emissions from network technology
installation"""

VAR_NETTECHCO2TRANS: str = "V_NetTechCo2Trans"
"""Name of variable for embodied CO2 emissions from network transmission"""

VAR_NETTECHCO2TOTAL: str = "V_NetTechCo2Total"
"""Name of variable for total network tech related CO2 emissions"""

CON_NETHUBIN: str = "C_NetHubIn"
"""Name of constraint for setting network hub inputs as sums over links"""

CON_NETHUBOUT: str = "C_NetHubOut"
"""Name of constraint for setting network hub outputs as sums over links"""

CON_NETLINKIN: str = "C_NetLinkIn"
"""Name of constraint for setting network link inputs as sums over network
techs"""

CON_NETLINKOUT: str = "C_NetLinkOut"
"""Name of constraint for setting network link outputs as sums over network
techs"""

CON_NETTRANSDYNAMIC: str = "C_NetTransDynamic"
"""Name of constraint for the network transmission dynamics"""

CON_NETTRANSSUMMIN: str = "C_NetTransSumMin"
"""Name of constraint for respecting lower thresholds for summed-up network
transmissions over time"""

CON_NETTRANSSUMMAX: str = "C_NetTransSumMax"
"""Name of constraint for respecting upper thresholds for summed-up network
transmissions over time"""

CON_YNETTECHUSED: str = "C_YNetTechUsed"
"""Name of constraint monitoring whether network tech usage"""

CON_NETTECHCAPMIN: str = "C_NetTechCapMin"
"""Name of constraint respecting minimal network tech capacity"""

CON_NETTECHCAPMAX: str = "C_NetTechCapMax"
"""Name of constraint respecting maximal network tech capacity"""

CON_NETTECHCAP: str = "C_NetTechCap"
"""Name of constraint setting network tech capacity from initial capacity and
installed capacity"""

CON_NETTECHTRANSCAPANDAVAILABILITY: str = "C_NetTechTransCapAndAvailability"
"""Name of constraint respecting network tech capacity and link availability
in network transmission"""

CON_YNETTECHINSTL: str = "C_YNetTechInstl"
"""Name of constraint monitoring whether any network tech installation occurs
at all"""

CON_NETTECHUNITCAPMIN: str = "C_NetTechUnitCapMin"
"""Name of constraint respecting the parameter 'unit_cap_min'"""

CON_NETTECHCOSTCAPEX: str = "C_NetTechCostCapex"
"""Name of constraint setting CAPEX costs for network tech installation"""

CON_NETTECHCOSTOPEXCAP: str = "C_NetTechCostOpexCap"
"""Name of constraint setting OPEX costs for network technology based on
capacity"""

CON_NETTECHCOSTOPEXTRANS: str = "C_NetTechCostOpexTrans"
"""Name of constraint setting OPEX costs for network technology based on
transmission amounts"""

CON_NETTECHCOSTTOTAL: str = "C_NetTechCostTotal"
"""Name of constraint setting total costs for network techs"""

CON_NETTECHCO2INSTL: str = "C_NetTechCo2Instl"
"""Name of constraint setting embodied CO2 emissions based on network tech
installation"""

CON_NETTECHCO2TRANS: str = "C_NetTechCo2Trans"
"""Name of constraint setting embodied CO2 emissions based on network
transmission"""

CON_NETTECHCO2TOTAL: str = "C_NetTechCo2Total"
"""Name of constraint setting total embodied CO2 emissions for networks"""


def build(
    model: Model,
    stages: Stages,
    hubs: Hubs,
    net_links: NetworkLinks,
    net_techs: NetworkTechs,
    times: Times,
) -> None:
    """
    Builds the network submodel. For a mathematical description in thorough
    detail, please refer to the section 'Network model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data object
    :type stages: Stages
    :param hubs: Hub data object
    :type hubs: Hubs
    :param net_links: Network link data object
    :type net_links: NetworkLinks
    :param net_techs: Network technology data object
    :type net_techs: NetworkTechs
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base_trans(model, hubs, net_links, net_techs, times)
    _build_base_cap(model, stages, net_links, net_techs)
    _build_cost(model, stages, net_links, net_techs, times)
    _build_co2(model, stages, net_links, net_techs, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built network module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base_trans(
    model: Model,
    hubs: Hubs,
    net_links: NetworkLinks,
    net_techs: NetworkTechs,
    times: Times,
) -> None:
    # [SET] Network Links
    setattr(model, SET_NETLINK, Set(initialize=[li.key for li in net_links.ids]))
    # [SET] Network techs
    setattr(model, SET_NETTECH, Set(initialize=[n.key for n in net_techs.ids]))
    # [SET] Tuples of (hub, link, ec) for which a network input could occur
    net_link_in = [
        (net_links.get_hub_start(li), li, e)
        for li in net_links.ids
        for e in net_links.get_ecs(li)
    ]
    net_link_in += [
        (net_links.get_hub_end(li), li, e)
        for li in net_links.ids
        for e in net_links.get_ecs(li)
        if net_links.is_bidirectional(li)
    ]
    setattr(
        model,
        SET_NETLINKIN,
        Set(
            within=(
                getattr(model, SET_HUB)
                * getattr(model, SET_NETLINK)
                * getattr(model, SET_EC)
            ),
            initialize=[(h.key, li.key, e.key) for (h, li, e) in net_link_in],
        ),
    )
    # [VAR] Network input for tuples (hub, link, ec), summed across net_techs
    setattr(
        model,
        VAR_NETLINKIN,
        Var(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKIN),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [SET] Tuples of (hub, link, ec) for which a network output could occur
    net_link_out = [
        (net_links.get_hub_end(li), li, e)
        for li in net_links.ids
        for e in net_links.get_ecs(li)
    ]
    net_link_out += [
        (net_links.get_hub_start(li), li, e)
        for li in net_links.ids
        for e in net_links.get_ecs(li)
        if net_links.is_bidirectional(li)
    ]
    setattr(
        model,
        SET_NETLINKOUT,
        Set(
            within=(
                getattr(model, SET_HUB)
                * getattr(model, SET_NETLINK)
                * getattr(model, SET_EC)
            ),
            initialize=[(h.key, li.key, e.key) for (h, li, e) in net_link_out],
        ),
    )
    # [VAR] Network output for tuples (hub, link, ec), summed across net_techs
    setattr(
        model,
        VAR_NETLINKOUT,
        Var(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKOUT),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )

    # [SET] Tuples of (hub, ec) for which a network input could occur
    net_hub_in = list(set([(h, e) for (h, _, e) in net_link_in]))
    setattr(
        model,
        SET_NETHUBIN,
        Set(
            within=(getattr(model, SET_HUB) * getattr(model, SET_EC)),
            initialize=[(h.key, e.key) for (h, e) in net_hub_in],
        ),
    )
    # [VAR] Network input for tuples (hub, ec), summed across links
    setattr(
        model,
        VAR_NETHUBIN,
        Var(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETHUBIN),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    getattr(model, VAR_NETHUBIN)
    # [SET] Tuples of (hub, ec) for which a network output could occur
    net_hub_out = list(set([(h, e) for (h, _, e) in net_link_out]))
    setattr(
        model,
        SET_NETHUBOUT,
        Set(
            within=getattr(model, SET_HUB) * getattr(model, SET_EC),
            initialize=[(h.key, e.key) for (h, e) in net_hub_out],
        ),
    )
    # [VAR] Network output for tuples (hub, ec), summed across links
    setattr(
        model,
        VAR_NETHUBOUT,
        Var(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETHUBOUT),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )

    # [CON] The hub_in/outs are the sum over all link_in/outs
    _con_net_hub_inout(model)

    # [SET] Tuples of (stage, link, net_tech) which are are allowed by TRL or
    #       allowed_net_tech_lists
    net_tech_tuple = [
        (s.key, li.key, n.key)
        for n in net_techs.ids
        for s in net_techs.get_allowed_stages(n)
        for li in net_techs.get_allowed_net_links(n)
    ]
    setattr(
        model,
        SET_NETTECHTUPLE,
        Set(
            initialize=net_tech_tuple,
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_NETLINK)
                * getattr(model, SET_NETTECH)
            ),
        ),
    )

    # [SET] Tuples of (stage, hub, link, net_tech) for which a network input
    #       could occur
    net_tech_in = [
        (s, h.key, li, n)
        for (s, li, n) in net_tech_tuple
        for h in hubs.ids
        if (h, NetLinkId(li), net_techs.get_ec(NetTechId(n))) in net_link_in
    ]
    setattr(
        model,
        SET_NETTECHIN,
        Set(
            initialize=net_tech_in,
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_NETLINK)
                * getattr(model, SET_NETTECH)
            ),
        ),
    )
    # [VAR] Network input for tuples (stage, hub, link, net_tech)
    setattr(
        model,
        VAR_NETTECHIN,
        Var(
            getattr(model, SET_NETTECHIN),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [SET] Tuples of (stage, hub, link, net_tech) for which a network output
    #       could occur
    net_tech_out = [
        (s, h.key, li, n)
        for (s, li, n) in net_tech_tuple
        for h in hubs.ids
        if (h, NetLinkId(li), net_techs.get_ec(NetTechId(n))) in net_link_out
    ]
    setattr(
        model,
        SET_NETTECHOUT,
        Set(
            initialize=net_tech_out,
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_NETLINK)
                * getattr(model, SET_NETTECH)
            ),
        ),
    )
    # [VAR] Network output for tuples (stage, hub, link, net_tech)
    setattr(
        model,
        VAR_NETTECHOUT,
        Var(
            getattr(model, SET_NETTECHOUT),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )

    # [CON] The link_in/outs are the sum over all tech_in/outs
    _con_net_link_inout(model, net_techs)
    # [CON] Transmissions dynamics including transmission loss per m
    _con_net_trans_dynamic(model, net_links, net_techs)
    # [CON] Constraints setting minimal and maximal summed-up transmissions
    _con_net_trans_sum_minmax(model, net_links, times)
    # [VAR] Binary monitoring network tech usage
    setattr(
        model, VAR_YNETTECHUSED, Var(getattr(model, SET_NETTECHTUPLE), domain=Binary)
    )
    # [CON] Network link usage (monitored over summed-up transmission)
    _con_net_tech_used(model, net_links, net_techs, times)


def _build_base_cap(
    model: Model, stages: Stages, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    # [VAR] Network tech capacity
    setattr(
        model,
        VAR_NETTECHCAP,
        Var(getattr(model, SET_NETTECHTUPLE), domain=NonNegativeReals),
    )
    # [SET] Tuples of links and ECs
    setattr(
        model,
        SET_NETLINKANDEC,
        Set(
            within=getattr(model, SET_NETLINK) * getattr(model, SET_EC),
            initialize=[
                (li.key, e.key) for li in net_links.ids for e in net_links.get_ecs(li)
            ],
        ),
    )
    # [CON] Minimal and maximal capacities (per link and EC)
    _con_net_tech_cap_minmax(model, net_links, net_techs)
    # [VAR] Newly installed network tech capacity
    setattr(
        model,
        VAR_NETTECHCAPINSTL,
        Var(getattr(model, SET_NETTECHTUPLE), domain=NonNegativeReals),
    )
    # [CON] Define NetTechCap as the sum of initial capacity and installed
    #       capacity from previous stages for which lifetime has not run out
    _con_net_tech_cap(model, stages, net_techs)
    # [CON] Respect network tech capacity (pertains to input power) and
    #       availability
    _con_net_tech_trans_cap_and_availability(model, net_links, net_techs)
    # [VAR] Binary monitoring new network tech installation
    setattr(
        model,
        VAR_YNETTECHCAPINSTL,
        Var(getattr(model, SET_NETTECHTUPLE), domain=Binary),
    )
    # [CON] Force YNetTechCapInstl to 1 if TechCapInstl is nonzero
    _con_y_net_tech_instl(model, net_links, net_techs)
    # Enforce the minimal unit capacity during installation
    _con_net_tech_unit_cap_min(model, net_techs)


def _build_cost(
    model: Model,
    stages: Stages,
    net_links: NetworkLinks,
    net_techs: NetworkTechs,
    times: Times,
) -> None:
    # [VAR] CAPEX cost
    setattr(
        model, VAR_NETTECHCOSTCAPEX, Var(getattr(model, SET_NETTECHTUPLE), domain=Reals)
    )
    # [CON] CAPEX cost
    _con_net_tech_cost_capex(model, stages, net_links, net_techs)
    # [VAR] OPEX (operation & maintenance) cost from capacity
    setattr(
        model,
        VAR_NETTECHCOSTOPEXCAP,
        Var(getattr(model, SET_NETTECHTUPLE), domain=Reals),
    )
    # [CON] OPEX cost from capacity
    _con_net_tech_cost_opex_cap(model, net_links, net_techs)
    # [VAR] OPEX (operation & maintenance) cost from transmission
    setattr(
        model,
        VAR_NETTECHCOSTOPEXTRANS,
        Var(getattr(model, SET_NETTECHTUPLE), domain=Reals),
    )
    # [CON] OPEX cost from transmission
    _con_net_tech_cost_opex_trans(model, net_links, net_techs, times)
    # [VAR] Total cost
    setattr(model, VAR_NETTECHCOSTTOTAL, Var(domain=Reals))
    # [CON] Total cost
    _con_net_tech_cost_total(model)


def _build_co2(
    model: Model,
    stages: Stages,
    net_links: NetworkLinks,
    net_techs: NetworkTechs,
    times: Times,
) -> None:
    # [VAR] CO2 emissions from installation
    setattr(
        model,
        VAR_NETTECHCO2INSTL,
        Var(getattr(model, SET_NETTECHTUPLE), domain=NonNegativeReals),
    )
    # [CON] CO2 emissions from installation
    _con_net_tech_co2_instl(model, stages, net_links, net_techs)
    # [VAR] CO2 emissions from transmission
    setattr(
        model,
        VAR_NETTECHCO2TRANS,
        Var(getattr(model, SET_NETTECHTUPLE), domain=NonNegativeReals),
    )
    # [CON] CO2 emissions from transmission
    _con_net_tech_co2_trans(model, net_links, net_techs, times)
    # [VAR] Total CO2 emissions from network techs
    setattr(
        model,
        VAR_NETTECHCO2TOTAL,
        Var(getattr(model, SET_STAGE), domain=NonNegativeReals),
    )
    # [CON] Total CO2 emissions from network techs
    _con_net_tech_co2_total(model)


def _con_net_hub_inout(model: Model) -> None:
    def __rule_net_hub_in(model, s, h, e, t):
        # Calculate sum of network link input
        net_link_in_sum = sum(
            getattr(model, VAR_NETLINKIN)[s, h, li, e, t]
            for li in getattr(model, SET_NETLINK)
            if (h, li, e) in getattr(model, SET_NETLINKIN)
        )
        # Set constraint
        return getattr(model, VAR_NETHUBIN)[s, h, e, t] == net_link_in_sum

    def __rule_net_hub_out(model, s, h, e, t):
        # Calculate sum of network link output
        net_link_out_sum = sum(
            getattr(model, VAR_NETLINKOUT)[s, h, li, e, t]
            for li in getattr(model, SET_NETLINK)
            if (h, li, e) in getattr(model, SET_NETLINKOUT)
        )
        # Set constraint
        return getattr(model, VAR_NETHUBOUT)[s, h, e, t] == net_link_out_sum

    setattr(
        model,
        CON_NETHUBIN,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETHUBIN),
            getattr(model, SET_TIME),
            rule=__rule_net_hub_in,
        ),
    )
    setattr(
        model,
        CON_NETHUBOUT,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETHUBOUT),
            getattr(model, SET_TIME),
            rule=__rule_net_hub_out,
        ),
    )


def _con_net_link_inout(model: Model, net_techs: NetworkTechs) -> None:
    def __rule_net_link_in(model, s, h, li, e, t):
        # Calculate sum of network tech input
        net_tech_in_sum = sum(
            getattr(model, VAR_NETTECHIN)[s, h, li, n, t]
            for n in getattr(model, SET_NETTECH)
            if EcId(e) == net_techs.get_ec(NetTechId(n))
            if (s, h, li, n) in getattr(model, SET_NETTECHIN)
        )
        # Set the constraint
        return getattr(model, VAR_NETLINKIN)[s, h, li, e, t] == net_tech_in_sum

    def __rule_net_link_out(model, s, h, li, e, t):
        # Calculate sum of network tech output
        net_tech_out_sum = sum(
            getattr(model, VAR_NETTECHOUT)[s, h, li, n, t]
            for n in getattr(model, SET_NETTECH)
            if EcId(e) == net_techs.get_ec(NetTechId(n))
            if (s, h, li, n) in getattr(model, SET_NETTECHOUT)
        )
        # Set the constraint
        return getattr(model, VAR_NETLINKOUT)[s, h, li, e, t] == net_tech_out_sum

    setattr(
        model,
        CON_NETLINKIN,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKIN),
            getattr(model, SET_TIME),
            rule=__rule_net_link_in,
        ),
    )
    setattr(
        model,
        CON_NETLINKOUT,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKOUT),
            getattr(model, SET_TIME),
            rule=__rule_net_link_out,
        ),
    )


def _con_net_trans_dynamic(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_net_trans_dynamic(model, s, h_out, li, n, t):
        # Get parameters
        trans_loss = net_techs.get_trans_loss(StageId(s), NetTechId(n))
        link_length = net_links.get_length(NetLinkId(li))
        # Get input hub for this link since h is output hub
        h_in = net_links.get_hub_start(NetLinkId(li))  # Forward case
        if HubId(h_out) == net_links.get_hub_start(NetLinkId(li)):
            h_in = net_links.get_hub_end(NetLinkId(li))  # Backward case
        # Calculate net_tech_out
        net_tech_out = (1 - trans_loss) ** link_length * getattr(model, VAR_NETTECHIN)[
            s, h_in.key, li, n, t
        ]
        # Set constraint
        return getattr(model, VAR_NETTECHOUT)[s, h_out, li, n, t] == net_tech_out

    setattr(
        model,
        CON_NETTRANSDYNAMIC,
        Constraint(
            getattr(model, SET_NETTECHOUT),
            getattr(model, SET_TIME),
            rule=__rule_net_trans_dynamic,
        ),
    )


def _con_net_trans_sum_minmax(
    model: Model, net_links: NetworkLinks, times: Times
) -> None:
    def __rule_net_trans_sum_min(model, s, h_out, li, e):
        # Get parameters
        link_dir = NetLinkDirection.FORWARD
        if HubId(h_out) == net_links.get_hub_start(NetLinkId(li)):
            link_dir = NetLinkDirection.BACKWARD
        trans_sum_min = net_links.get_sum_min(
            StageId(s), NetLinkId(li), EcId(e), link_dir
        )
        # Calculate summed-up transmission
        trans_sum = sum(
            (
                times.get_weight(StageId(s), TimeId(t))
                * getattr(model, VAR_NETLINKOUT)[s, h_out, li, e, t]
            )
            for t in getattr(model, SET_TIME)
        )
        # Avoid trivial case
        if isinstance(trans_sum, int) and trans_sum == 0:
            return Constraint.Skip
        # Set the constraint
        return trans_sum >= trans_sum_min

    def __rule_net_trans_sum_max(model, s, h_out, li, e):
        # Get parameters
        link_dir = NetLinkDirection.FORWARD
        if HubId(h_out) == net_links.get_hub_start(NetLinkId(li)):
            link_dir = NetLinkDirection.BACKWARD
        trans_sum_max = net_links.get_sum_max(
            StageId(s), NetLinkId(li), EcId(e), link_dir
        )
        # Calculate summed-up transmission
        trans_sum = sum(
            (
                times.get_weight(StageId(s), TimeId(t))
                * getattr(model, VAR_NETLINKOUT)[s, h_out, li, e, t]
            )
            for t in getattr(model, SET_TIME)
        )
        # Avoid trivial case
        if isinstance(trans_sum, int) and trans_sum == 0:
            return Constraint.Skip
        # Set the constraint
        return trans_sum <= trans_sum_max

    setattr(
        model,
        CON_NETTRANSSUMMIN,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKOUT),
            rule=__rule_net_trans_sum_min,
        ),
    )
    setattr(
        model,
        CON_NETTRANSSUMMAX,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKOUT),
            rule=__rule_net_trans_sum_max,
        ),
    )


def _con_net_tech_used(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs, times: Times
) -> None:
    def __rule_net_tech_used(model, s, li, n):
        # Parameter
        ec = net_techs.get_ec(NetTechId(n))
        cap_max = net_links.get_cap_max(StageId(s), NetLinkId(li), ec)
        # Calculate bigM for link capacity of this net_tech's ec
        big_m = getattr(model, PAR_BIGMGENERIC) * times.num_horizon_ts
        if cap_max < float("inf"):
            big_m = common.EPS_BIGM + cap_max * times.num_horizon_ts
        else:
            logging.log_file_warning(
                f"cap_max[{s}, {li}, {ec}] not available to calculate a big-M "
                "value for summed-up link input. Using generic big-M "
                f"value {getattr(model, PAR_BIGMGENERIC).value} based on "
                "demands instead",
                module=LOG_MODULE_STR,
            )
        # Get summed-up input for this link from both hubs
        net_in_sum = sum(
            (
                times.get_weight(StageId(s), TimeId(t))
                * getattr(model, VAR_NETTECHIN)[s, h, li, n, t]
            )
            for h in getattr(model, SET_HUB)
            for t in getattr(model, SET_TIME)
            if (s, h, li, n) in getattr(model, SET_NETTECHIN)
        )
        # Set the constraint
        return net_in_sum <= big_m * getattr(model, VAR_YNETTECHUSED)[s, li, n]

    setattr(
        model,
        CON_YNETTECHUSED,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_used),
    )


def _con_net_tech_cap_minmax(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_net_tech_cap_min(model, s, li, e):
        # Parameter
        cap_min = net_links.get_cap_min(StageId(s), NetLinkId(li), EcId(e))
        # Calculate capacity across all network techs that share this EC
        cap_sum = sum(
            getattr(model, VAR_NETTECHCAP)[s, li, n]
            for (s_, li_, n) in getattr(model, SET_NETTECHTUPLE)
            if s == s_
            if li == li_
            if EcId(e) == net_techs.get_ec(NetTechId(n))
        )
        # Skip empty constraint
        if isinstance(cap_sum, int) and cap_sum == 0:
            return Constraint.Skip
        # Set constraint
        return cap_sum >= cap_min

    def __rule_net_tech_cap_max(model, s, li, e):
        # Parameter
        cap_max = net_links.get_cap_max(StageId(s), NetLinkId(li), EcId(e))
        # Calculate capacity across all network techs that share this EC
        cap_sum = sum(
            getattr(model, VAR_NETTECHCAP)[s, li, n]
            for (s_, li_, n) in getattr(model, SET_NETTECHTUPLE)
            if s == s_
            if li == li_
            if EcId(e) == net_techs.get_ec(NetTechId(n))
        )
        # Skip empty constraint
        if isinstance(cap_sum, int) and cap_sum == 0:
            return Constraint.Skip
        # Set constraint
        return cap_sum <= cap_max

    setattr(
        model,
        CON_NETTECHCAPMIN,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKANDEC),
            rule=__rule_net_tech_cap_min,
        ),
    )
    setattr(
        model,
        CON_NETTECHCAPMAX,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_NETLINKANDEC),
            rule=__rule_net_tech_cap_max,
        ),
    )


def _con_net_tech_cap(model: Model, stages: Stages, net_techs: NetworkTechs) -> None:
    def __rule_net_tech_cap(model, s, li, n):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        net_tech_lifetime = net_techs.get_lifetime(NetTechId(n))
        age_init = net_techs.get_age_init(NetLinkId(li), NetTechId(n))
        cap_init = net_techs.get_cap_init(NetLinkId(li), NetTechId(n))
        net_tech_cap = 0
        # Initial capacity
        if current_year - stages.init_year < net_tech_lifetime - age_init:
            net_tech_cap += cap_init
        # Capacity installed during previous stages
        for s_instl in getattr(model, SET_STAGE):
            # Check current stage is within lifetim eof installed tech
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= net_tech_lifetime:
                continue
            # Add installed capacity to total
            net_tech_cap += getattr(model, VAR_NETTECHCAPINSTL)[s_instl, li, n]
        # Set constraint
        return getattr(model, VAR_NETTECHCAP)[s, li, n] == net_tech_cap

    setattr(
        model,
        CON_NETTECHCAP,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_cap),
    )


def _con_net_tech_trans_cap_and_availability(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_net_tech_trans_cap_and_availability(model, s, li, n, t):
        # Get parameters
        e = net_techs.get_ec(NetTechId(n))
        availability = net_links.get_availability(
            StageId(s), NetLinkId(li), e
        ).get_value(TimeId(t))
        # Get inputs for this network tech from both hubs
        net_tech_in = sum(
            getattr(model, VAR_NETTECHIN)[s, h, li, n, t]
            for h in getattr(model, SET_HUB)
            if (s, h, li, n) in getattr(model, SET_NETTECHIN)
        )
        # Set constraint
        return net_tech_in <= availability * getattr(model, VAR_NETTECHCAP)[s, li, n]

    setattr(
        model,
        CON_NETTECHTRANSCAPANDAVAILABILITY,
        Constraint(
            getattr(model, SET_NETTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_net_tech_trans_cap_and_availability,
        ),
    )


def _con_y_net_tech_instl(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_y_net_tech_instl(model, s, li, n):
        # BigM parameter for network tech capacity
        big_m = getattr(model, PAR_BIGMGENERIC)
        ec = net_techs.get_ec(NetTechId(n))
        cap_max = net_links.get_cap_max(StageId(s), NetLinkId(li), ec)
        if cap_max < float("inf"):
            big_m = cap_max + common.EPS_BIGM
        # Set constraint
        return (
            getattr(model, VAR_NETTECHCAPINSTL)[s, li, n]
            <= big_m * getattr(model, VAR_YNETTECHCAPINSTL)[s, li, n]
        )

    setattr(
        model,
        CON_YNETTECHINSTL,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_y_net_tech_instl),
    )


def _con_net_tech_unit_cap_min(model: Model, net_techs: NetworkTechs) -> None:
    def __rule_net_tech_unit_cap_min(model, s, li, n):
        unit_cap_min = net_techs.get_unit_cap_min(StageId(s), NetTechId(n))
        return getattr(model, VAR_NETTECHCAPINSTL)[s, li, n] >= (
            unit_cap_min * getattr(model, VAR_YNETTECHCAPINSTL)[s, li, n]
        )

    setattr(
        model,
        CON_NETTECHUNITCAPMIN,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_unit_cap_min),
    )


def _con_net_tech_cost_capex(
    model: Model, stages: Stages, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_net_tech_cost_capex(model, s, li, n):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        link_length = net_links.get_length(NetLinkId(li))
        interest_rate = net_techs.get_interest_rate(NetTechId(n))
        net_tech_lifetime = net_techs.get_lifetime(NetTechId(n))
        crf = calculate_crf(interest_rate, net_tech_lifetime)
        cost_capex = 0
        # Installation stages
        for s_instl in getattr(model, SET_STAGE):
            # Check current stage is within lifetim eof installed tech
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= net_tech_lifetime:
                continue
            # Installation-stage-dependent parameters
            capex_per_cap = net_techs.get_capex_per_cap(StageId(s_instl), NetTechId(n))
            one_time_capex = net_techs.get_one_time_capex(
                StageId(s_instl), NetTechId(n)
            )
            # One-time capex costs (if installation occured)
            cost_capex += (
                crf
                * one_time_capex
                * getattr(model, VAR_YNETTECHCAPINSTL)[s_instl, li, n]
            )
            # Per-capacity capex costs
            cost_capex += (
                crf
                * capex_per_cap
                * getattr(model, VAR_NETTECHCAPINSTL)[s_instl, li, n]
            )
        # Multiply cost with link length
        cost_capex *= link_length
        # Set constraint
        return getattr(model, VAR_NETTECHCOSTCAPEX)[s, li, n] == cost_capex

    setattr(
        model,
        CON_NETTECHCOSTCAPEX,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_cost_capex),
    )


def _con_net_tech_cost_opex_cap(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_net_tech_cost_opex_cap(model, s, li, n):
        # Parameters
        link_length = net_links.get_length(NetLinkId(li))
        opex_per_cap = net_techs.get_opex_per_cap(StageId(s), NetTechId(n))
        one_time_opex = net_techs.get_one_time_opex(StageId(s), NetTechId(n))
        # Calculate OPEX cost
        cost_opex_instl = (
            one_time_opex * getattr(model, VAR_YNETTECHUSED)[s, li, n]
            + opex_per_cap * getattr(model, VAR_NETTECHCAP)[s, li, n]
        )
        # Multiply cost with link length
        cost_opex_instl *= link_length
        # Set constraint
        return getattr(model, VAR_NETTECHCOSTOPEXCAP)[s, li, n] == cost_opex_instl

    setattr(
        model,
        CON_NETTECHCOSTOPEXCAP,
        Constraint(
            getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_cost_opex_cap
        ),
    )


def _con_net_tech_cost_opex_trans(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs, times: Times
) -> None:
    def __rule_net_tech_cost_opex_trans(model, s, li, n):
        # Parameters
        link_length = net_links.get_length(NetLinkId(li))
        opex_per_energy = net_techs.get_opex_per_energy(StageId(s), NetTechId(n))
        # Get summed-up input for this link from both hubs
        net_in_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_NETTECHIN)[s, h, li, n, t]
            for h in getattr(model, SET_HUB)
            for t in getattr(model, SET_TIME)
            if (s, h, li, n) in getattr(model, SET_NETTECHIN)
        )
        # Calculate OPEX from transmission cost
        cost_opex_trans = opex_per_energy * net_in_sum
        # Multiply cost with link length
        cost_opex_trans *= link_length
        # Set constraint
        return getattr(model, VAR_NETTECHCOSTOPEXTRANS)[s, li, n] == cost_opex_trans

    setattr(
        model,
        CON_NETTECHCOSTOPEXTRANS,
        Constraint(
            getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_cost_opex_trans
        ),
    )


def _con_net_tech_cost_total(model: Model) -> None:
    def __rule_net_tech_cost_total(model):
        # Calculate the total network tech cost
        net_tech_cost_total = sum(
            getattr(model, VAR_NETTECHCOSTCAPEX)[s, li, n]
            + getattr(model, VAR_NETTECHCOSTOPEXCAP)[s, li, n]
            + getattr(model, VAR_NETTECHCOSTOPEXTRANS)[s, li, n]
            for (s, li, n) in getattr(model, SET_NETTECHTUPLE)
        )
        # Set the constraint
        return getattr(model, VAR_NETTECHCOSTTOTAL) == net_tech_cost_total

    setattr(model, CON_NETTECHCOSTTOTAL, Constraint(rule=__rule_net_tech_cost_total))


def _con_net_tech_co2_instl(
    model: Model, stages: Stages, net_links: NetworkLinks, net_techs: NetworkTechs
) -> None:
    def __rule_net_tech_co2_instl(model, s, li, n):
        # Parameters
        link_length = net_links.get_length(NetLinkId(li))
        current_year = stages.get_start_year(StageId(s))
        net_tech_lifetime = net_techs.get_lifetime(NetTechId(n))
        co2_per_cap = net_techs.get_co2_per_cap(StageId(s), NetTechId(n))
        co2_instl = 0
        # Installation stages
        for s_instl in getattr(model, SET_STAGE):
            # Check current stage is within lifetime of installed tech
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= net_tech_lifetime:
                continue
            # Add the CO2 for the current stage
            co2_instl += (
                co2_per_cap
                * getattr(model, VAR_NETTECHCAPINSTL)[s_instl, li, n]
                / net_tech_lifetime
            )
        # Multiply emissions with link length
        co2_instl *= link_length
        # Set constraint
        return getattr(model, VAR_NETTECHCO2INSTL)[s, li, n] == co2_instl

    setattr(
        model,
        CON_NETTECHCO2INSTL,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_co2_instl),
    )


def _con_net_tech_co2_trans(
    model: Model, net_links: NetworkLinks, net_techs: NetworkTechs, times: Times
) -> None:
    def __rule_net_tech_co2_trans(model, s, li, n):
        # Parameters
        link_length = net_links.get_length(NetLinkId(li))
        co2_per_energy = net_techs.get_co2_per_energy(StageId(s), NetTechId(n))
        # Get summed-up input for this link from both hubs
        net_in_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_NETTECHIN)[s, h, li, n, t]
            for h in getattr(model, SET_HUB)
            for t in getattr(model, SET_TIME)
            if (s, h, li, n) in getattr(model, SET_NETTECHIN)
        )
        # Calculate CO2 for transmissions
        co2_trans = co2_per_energy * net_in_sum
        # Multiply CO2 with link length
        co2_trans *= link_length
        # Set constraint
        return getattr(model, VAR_NETTECHCO2TRANS)[s, li, n] == co2_trans

    setattr(
        model,
        CON_NETTECHCO2TRANS,
        Constraint(getattr(model, SET_NETTECHTUPLE), rule=__rule_net_tech_co2_trans),
    )


def _con_net_tech_co2_total(model: Model) -> None:
    def __rule_net_tech_co2_total(model, s):
        # Calculate the total network tech CO2
        net_tech_co2_total = sum(
            getattr(model, VAR_NETTECHCO2INSTL)[s, li, n]
            + getattr(model, VAR_NETTECHCO2TRANS)[s, li, n]
            for (s_, li, n) in getattr(model, SET_NETTECHTUPLE)
            if s == s_
        )
        # Set the constraint
        return getattr(model, VAR_NETTECHCO2TOTAL)[s] == net_tech_co2_total

    setattr(
        model,
        CON_NETTECHCO2TOTAL,
        Constraint(getattr(model, SET_STAGE), rule=__rule_net_tech_co2_total),
    )
