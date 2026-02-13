param location string = 'koreacentral'
param iotHubName string = 'aziothub'
param asaJobName string = 'streamanalytics'
param iotHubSkuName string = 'S1'
param iotHubSkuCapacity int = 1
param asaStreamingUnits int = 3
param useUniqueSuffix bool = true
param ipRules array = [
  {
    filterName: 'office-1'
    action: 'Allow'
    ipMask: '59.12.125.187'
  }
  {
    filterName: 'vm-1'
    action: 'Allow'
    ipMask: '20.41.123.99'
  }
]

resource iotHub 'Microsoft.Devices/IotHubs@2023-06-30' = {
  name: useUniqueSuffix ? toLower('${iotHubName}-${uniqueString(resourceGroup().id)}') : iotHubName
  location: location
  sku: {
    name: iotHubSkuName
    capacity: iotHubSkuCapacity
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    minTlsVersion: '1.2'
    networkRuleSets: {
      defaultAction: 'Allow'
      applyToBuiltInEventHubEndpoint: true
      ipRules: ipRules
    }
    routing: {
      endpoints: {
        serviceBusQueues: []
        serviceBusTopics: []
        eventHubs: []
        storageContainers: []
        cosmosDBSqlContainers: []
      }
      routes: []
      fallbackRoute: {
        name: '$fallback'
        source: 'DeviceMessages'
        condition: 'true'
        endpointNames: [
          'events'
        ]
        isEnabled: true
      }
    }
  }
}

resource asaJob 'Microsoft.StreamAnalytics/streamingjobs@2021-10-01-preview' = {
  name: asaJobName
  location: location
  sku: {
    name: 'StandardV2'
    capacity: asaStreamingUnits
  }
  properties: {
    sku: {
      name: 'StandardV2'
    }
    jobType: 'Cloud'
    dataLocale: 'en-US'
    compatibilityLevel: '1.2'
    eventsOutOfOrderPolicy: 'Adjust'
    eventsOutOfOrderMaxDelayInSeconds: 0
    eventsLateArrivalMaxDelayInSeconds: 5
    outputErrorPolicy: 'Drop'
  }
}

resource asaTransformation 'Microsoft.StreamAnalytics/streamingjobs/transformations@2020-03-01' = {
  name: '${asaJob.name}/default'
  properties: {
    streamingUnits: asaStreamingUnits
    query: '-- TODO: Add ASA query'
  }
}
