open System
open Confluent.Kafka
open System.Text.Json
open System.Threading

type ShipmentEvent = {
    shipment_id: string
    status: string
    origin: string
    destination: string
    timestamp: string
}

[<EntryPoint>]
let main argv =
    let config = ProducerConfig(BootstrapServers = "localhost:19092")
    let statuses = [| "BOOKED"; "PICKED_UP"; "IN_TRANSIT"; "DELIVERED" |]
    let locations = [| "CNSHA"; "USLAX"; "USCHI"; "DEHAM"; "NLRTM" |]
    
    // Line 22: The 'using' block starts here. 
    // Ensure the (fun p -> ...) block is indented correctly.
    using (ProducerBuilder<string, string>(config).Build()) (fun p ->
        printfn "🚛 Freight Event Simulator Started. Press Ctrl+C to stop."
        let rng = Random()

        while true do
            let event = {
                shipment_id = sprintf "SHIP-%d" (rng.Next(1000, 9999))
                status = statuses.[rng.Next(statuses.Length)]
                origin = locations.[rng.Next(locations.Length)]
                destination = locations.[rng.Next(locations.Length)]
                timestamp = DateTime.UtcNow.ToString("o")
            }
            
            let payload = JsonSerializer.Serialize(event)
            let message = Message<string, string>(Key = event.shipment_id, Value = payload)
            
            // Produce to the topic
            p.Produce("freight-events", message, (fun (dr: DeliveryReport<string, string>) ->
                if dr.Error.IsError then
                    printfn "❌ Error: %s" dr.Error.Reason
                else
                    printfn "📤 Sent: %s | Status: %s" event.shipment_id event.status
            ))
            
            Thread.Sleep(2000)
    )
    0 // This 0 must be aligned with the first 'let' (line 17)
