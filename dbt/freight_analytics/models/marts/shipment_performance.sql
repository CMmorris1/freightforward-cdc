{{ config(materialized='table') }}

with raw_data as (
    select * from {{ source('raw_freight', 'fct_shipment_tracking') }}
),

-- shipment_lifecycles as (
--     select
--         shipment_id,
--         min(last_update) as booked_at,
--         max(last_update) as latest_update,
--         count(distinct current_status) as status_changes,
--         -- Senior Logic: Check if it's actually delivered
--         max(case when current_status = 'DELIVERED' then last_update end) as delivered_at
--     from raw_data
--     group by 1
-- )

-- select
--     *,
--     -- Calculate Lead Time in hours
--     extract(epoch from (delivered_at - booked_at)) / 3600 as lead_time_hours
-- from shipment_lifecycles
